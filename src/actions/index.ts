import { defineAction } from 'astro:actions';
import { z } from 'astro:schema';
import { db } from '../db';
import { pastSemester, retakes, retakeTeachers, teachersLocal } from '../db/schema';
import { eq, inArray } from 'drizzle-orm';

export const server = {
    scheduleOptions: {
        createRetake: defineAction({
            accept: 'json',
            input: z.object({
                groupUuid: z.string(),
                subjectUuid: z.string(),
                date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, "Формат даты: YYYY-MM-DD"),
                timeSlots: z.array(z.number().min(1).max(7)),
                roomUuid: z.string().optional(),
                link: z.string().optional(),
                attemptNumber: z.number().min(1).max(3).default(1),
                mainTeachersUuids: z.array(z.string()).min(1),
                commissionTeachersUuids: z.array(z.string()).optional(),
                chairmanUuid: z.string().optional(),
            }),
            handler: async (input, context) => {
                const userId = context.locals.user?.id;
                if (!userId) throw new Error("Вы не авторизованы!");

                try {
                    await db.transaction(async (tx) => {
                        const [newRetake] = await tx.insert(retakes).values({
                            groupUuid: input.groupUuid,
                            subjectUuid: input.subjectUuid,
                            date: input.date,
                            timeSlots: input.timeSlots,
                            roomUuid: input.roomUuid,
                            link: input.link,
                            attemptNumber: input.attemptNumber,
                            createdBy: String(userId),
                        }).returning({ id: retakes.id });

                        const teacherLinks = [];
                        for (const uuid of input.mainTeachersUuids) {
                            teacherLinks.push({ retakeId: newRetake.id, teacherUuid: uuid, role: 'MAIN' });
                        }
                        if (input.chairmanUuid) {
                            teacherLinks.push({ retakeId: newRetake.id, teacherUuid: input.chairmanUuid, role: 'CHAIRMAN' });
                        }
                        if (input.commissionTeachersUuids) {
                            for (const uuid of input.commissionTeachersUuids) {
                                teacherLinks.push({ retakeId: newRetake.id, teacherUuid: uuid, role: 'COMMISSION' });
                            }
                        }
                        await tx.insert(retakeTeachers).values(teacherLinks);
                    });
                    return { success: true, message: "Пересдача успешно назначена!" };
                } catch (error) {
                    console.error(error);
                    throw new Error("Не удалось сохранить расписание.");
                }
            }
        }),
        getGroupHistory: defineAction({
            accept: 'json',
            input: z.object({ groupName: z.string() }),
            handler: async ({ groupName }) => {
                return await db.select({
                    subjectName: pastSemester.subjectName,
                    teacherNames: pastSemester.teacherNames
                }).from(pastSemester).where(eq(pastSemester.groupName, groupName));
            }
        }),
        getGroupRetakes: defineAction({
            accept: 'json',
            input: z.object({ groupUuid: z.string() }),
            handler: async ({ groupUuid }) => {
                return await db.select({
                    id: retakes.id,
                    subjectUuid: retakes.subjectUuid,
                    attemptNumber: retakes.attemptNumber,
                    date: retakes.date,
                    createdBy: retakes.createdBy
                }).from(retakes).where(eq(retakes.groupUuid, groupUuid));
            }
        }),
        deleteRetake: defineAction({
            accept: 'json',
            input: z.object({ id: z.string().uuid() }),
            handler: async ({ id }, context) => {
                const user = context.locals.user;
                if (!user) throw new Error("Вы не авторизованы");

                const [retake] = await db.select().from(retakes).where(eq(retakes.id, id));
                if (!retake) throw new Error("Пересдача не найдена");

                if (user.role !== 'ADMIN' && retake.createdBy !== String(user.id)) {
                    throw new Error("Вы можете удалять только те пересдачи, которые назначили сами");
                }

                await db.delete(retakeTeachers).where(eq(retakeTeachers.retakeId, id));
                await db.delete(retakes).where(eq(retakes.id, id));

                return { success: true };
            }
        }),
        getMergedDaySchedule: defineAction({
            accept: 'json',
            input: z.object({
                groupNumber: z.string(),
                groupUuid: z.string(),
                teacherUuids: z.array(z.string()),
                teacherNames: z.array(z.string()),
                date: z.string()
            }),
            handler: async ({ groupNumber, groupUuid, teacherUuids, teacherNames, date }) => {
                const { RaspyxAPI } = await import('../lib/api-client');
                const dateObj = new Date(date);
                const daysOfWeek = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'];
                const dayOfWeekString = daysOfWeek[dateObj.getDay()];

                if (dayOfWeekString === 'sunday') {
                    return { "1": null, "2": null, "3": null, "4": null, "5": null, "6": null, "7": null };
                }

                const mergedDay: Record<string, any> = { "1": null, "2": null, "3": null, "4": null, "5": null, "6": null, "7": null };
                const targetTime = dateObj.getTime();

                try {
                    const dbRetakes = await db.select().from(retakes).where(eq(retakes.date, date));

                    if (dbRetakes.length > 0) {
                        const groupRetakes = dbRetakes.filter(r => r.groupUuid === groupUuid);
                        groupRetakes.forEach(r => {
                            r.timeSlots.forEach(slot => {
                                mergedDay[slot] = {
                                    reason: 'Занято (Пересдача)',
                                    details: {
                                        subject: 'Назначена пересдача в системе',
                                        type: `Попытка ${r.attemptNumber}`,
                                        location: r.link ? 'Онлайн' : (r.roomUuid || 'Очно')
                                    }
                                };
                            });
                        });

                        if (teacherUuids.length > 0) {
                            const busyTeachers = await db.select({
                                retakeId: retakeTeachers.retakeId,
                                teacherUuid: retakeTeachers.teacherUuid,
                                fullName: teachersLocal.fullName
                            }).from(retakeTeachers).innerJoin(teachersLocal, eq(retakeTeachers.teacherUuid, teachersLocal.uuid)).where(inArray(retakeTeachers.retakeId, dbRetakes.map(r => r.id)));

                            busyTeachers.forEach(bt => {
                                if (teacherUuids.includes(bt.teacherUuid)) {
                                    const retake = dbRetakes.find(r => r.id === bt.retakeId);
                                    if (retake) {
                                        retake.timeSlots.forEach(slot => {
                                            const shortName = bt.fullName.split(' ')[0];
                                            if (!mergedDay[slot] || !mergedDay[slot].reason.includes(shortName)) {
                                                mergedDay[slot] = {
                                                    reason: `Занято (Пересдача у: ${shortName})`,
                                                    details: { subject: 'Принимает пересдачу', type: 'Комиссия', location: 'В системе' }
                                                };
                                            }
                                        });
                                    }
                                }
                            });
                        }
                    }

                    const groupRes = await RaspyxAPI.getGroupSchedule(groupNumber);
                    const groupDay = groupRes?.result?.[dayOfWeekString];
                    if (groupDay) {
                        for (let i = 1; i <= 7; i++) {
                            const activePair = groupDay[i.toString()]?.find((p: any) => {
                                if (!p.start_date || !p.end_date) return true;
                                const start = new Date(p.start_date).getTime();
                                const end = new Date(p.end_date).getTime();
                                return targetTime >= start && targetTime <= end;
                            });

                            if (activePair) {
                                const prevReason = mergedDay[i] ? `${mergedDay[i].reason} + Пара` : 'Занято у группы (По расписанию)';
                                mergedDay[i] = {
                                    reason: prevReason,
                                    details: {
                                        subject: activePair.subject?.name || 'Предмет не указан',
                                        type: activePair.subject_type?.type || 'Тип не указан',
                                        location: activePair.location?.name ? `${activePair.location.name} (${activePair.rooms?.[0]?.number || ''})` : 'Аудитория не указана'
                                    }
                                };
                            }
                        }
                    }

                    for (const tName of teacherNames) {
                        const teacherRes = await RaspyxAPI.getTeacherSchedule(tName);
                        const teacherDay = teacherRes?.result?.[dayOfWeekString];

                        if (teacherDay) {
                            for (let i = 1; i <= 7; i++) {
                                const activePair = teacherDay[i.toString()]?.find((p: any) => {
                                    if (!p.start_date || !p.end_date) return true;
                                    const start = new Date(p.start_date).getTime();
                                    const end = new Date(p.end_date).getTime();
                                    return targetTime >= start && targetTime <= end;
                                });

                                if (activePair) {
                                    const shortName = tName.split(' ')[0];
                                    if (!mergedDay[i]) {
                                        mergedDay[i] = {
                                            reason: `Пара у: ${shortName}`,
                                            details: {
                                                subject: activePair.subject?.name || 'Предмет',
                                                type: activePair.subject_type?.type || 'Тип',
                                                location: activePair.location?.name ? `${activePair.location.name} (${activePair.rooms?.[0]?.number || ''})` : 'Аудитория'
                                            }
                                        };
                                    } else if (!mergedDay[i].reason.includes(shortName)) {
                                        mergedDay[i].reason += ` + ${shortName}`;
                                    }
                                }
                            }
                        }
                    }

                    return mergedDay;
                } catch (e) {
                    console.error("Ошибка при слиянии расписаний:", e);
                    return mergedDay;
                }
            }
        }),
    }
};
