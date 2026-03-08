import { defineAction } from 'astro:actions';
import { z } from 'astro:schema';
import { db } from '../db';
import { retakes, retakeTeachers, users, teachersLocal, pastSemester, departments } from '../db/schema';
import { eq, inArray, sql } from 'drizzle-orm';
import { Argon2id } from 'oslo/password';
import { lucia } from '../lib/auth';

export const server = {
    auth: {
        login: defineAction({
            accept: 'form',
            input: z.object({
                username: z.string(),
                password: z.string(),
            }),
            handler: async ({ username, password }, context) => {
                const [user] = await db.select().from(users).where(eq(users.username, username));
                if (!user) throw new Error("Неверный логин или пароль");

                const validPassword = await new Argon2id().verify(user.passwordHash, password);
                if (!validPassword) throw new Error("Неверный логин или пароль");

                const session = await lucia.createSession(user.id, {});
                const sessionCookie = lucia.createSessionCookie(session.id);
                context.cookies.set(sessionCookie.name, sessionCookie.value, sessionCookie.attributes);

                return { success: true };
            }
        }),

        logout: defineAction({
            handler: async (_, context) => {
                if (!context.locals.session) return { success: false };
                await lucia.invalidateSession(context.locals.session.id);
                const sessionCookie = lucia.createBlankSessionCookie();
                context.cookies.set(sessionCookie.name, sessionCookie.value, sessionCookie.attributes);
                return { success: true };
            }
        }),

        changePassword: defineAction({
            accept: 'form',
            input: z.object({
                currentPassword: z.string(),
                newPassword: z.string().min(6, "Новый пароль должен быть не менее 6 символов"),
            }),
            handler: async ({ currentPassword, newPassword }, context) => {
                const user = context.locals.user;
                if (!user) throw new Error("Вы не авторизованы");

                const [dbUser] = await db.select().from(users).where(eq(users.id, user.id));
                if (!dbUser) throw new Error("Пользователь не найден");

                const validPassword = await new Argon2id().verify(dbUser.passwordHash, currentPassword);
                if (!validPassword) throw new Error("Текущий пароль введен неверно");

                const hashedNewPassword = await new Argon2id().hash(newPassword);
                await db.update(users).set({ passwordHash: hashedNewPassword }).where(eq(users.id, user.id));

                return { success: true, message: "Пароль успешно изменен!" };
            }
        })
    },

    admin: {
        updateTeacherDept: defineAction({
            accept: 'json',
            input: z.object({
                teacherUuid: z.string(),
                departmentIds: z.array(z.number())
            }),
            handler: async ({ teacherUuid, departmentIds }, context) => {
                if (context.locals.user?.role !== 'ADMIN') throw new Error("Отказано в доступе");
                await db.update(teachersLocal).set({ departmentIds }).where(eq(teachersLocal.uuid, teacherUuid));
                return { success: true };
            }
        }),

        createProfile: defineAction({
            accept: 'json',
            input: z.object({
                teacherUuid: z.string(),
                username: z.string().min(3),
                password: z.string().min(6),
                departmentIds: z.array(z.number()),
                role: z.enum(["TEACHER", "EMPLOYEE"]).default("TEACHER")
            }),
            handler: async (input, context) => {
                if (context.locals.user?.role !== 'ADMIN') throw new Error("Отказано в доступе");

                const [existing] = await db.select().from(users).where(eq(users.username, input.username));
                if (existing) throw new Error("Пользователь с таким логином уже существует");

                const newUserId = crypto.randomUUID();
                const hashedPassword = await new Argon2id().hash(input.password);

                await db.insert(users).values({
                    id: newUserId,
                    username: input.username,
                    passwordHash: hashedPassword,
                    role: input.role,
                    departmentIds: input.departmentIds,
                    teacherUuid: input.teacherUuid
                });

                return { success: true, message: "Профиль успешно создан!" };
            }
        }),

        changeRole: defineAction({
            accept: 'json',
            input: z.object({
                teacherUuid: z.string(),
                newRole: z.enum(["TEACHER", "EMPLOYEE"])
            }),
            handler: async ({ teacherUuid, newRole }, context) => {
                if (context.locals.user?.role !== 'ADMIN') throw new Error("Отказано в доступе");
                await db.update(users).set({ role: newRole }).where(eq(users.teacherUuid, teacherUuid));
                return { success: true };
            }
        }),

        addDepartment: defineAction({
            accept: 'json',
            input: z.object({ name: z.string().min(2, "Название слишком короткое") }),
            handler: async ({ name }, context) => {
                if (context.locals.user?.role !== 'ADMIN') throw new Error("Отказано в доступе");
                const [newDept] = await db.insert(departments).values({ name }).returning();
                return { success: true, department: newDept };
            }
        }),

        updateDepartment: defineAction({
            accept: 'json',
            input: z.object({ id: z.number(), name: z.string().min(2) }),
            handler: async ({ id, name }, context) => {
                if (context.locals.user?.role !== 'ADMIN') throw new Error("Отказано в доступе");
                await db.update(departments).set({ name }).where(eq(departments.id, id));
                return { success: true };
            }
        }),

        deleteDepartment: defineAction({
            accept: 'json',
            input: z.object({ id: z.number() }),
            handler: async ({ id }, context) => {
                if (context.locals.user?.role !== 'ADMIN') throw new Error("Отказано в доступе");
                await db.update(teachersLocal).set({ departmentIds: sql`array_remove(${teachersLocal.departmentIds}, ${id})` });
                await db.update(users).set({ departmentIds: sql`array_remove(${users.departmentIds}, ${id})` });
                await db.delete(departments).where(eq(departments.id, id));
                return { success: true };
            }
        })
    },

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
                            roomUuid: input.roomUuid, // Теперь это текст, ошибки не будет
                            link: input.link,
                            attemptNumber: input.attemptNumber,
                            createdBy: userId,
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
            input: z.object({ id: z.coerce.number() }),
            handler: async ({ id }, context) => {
                const user = context.locals.user;
                if (!user) throw new Error("Вы не авторизованы");

                const [retake] = await db.select().from(retakes).where(eq(retakes.id, id));
                if (!retake) throw new Error("Пересдача не найдена");

                if (user.role !== 'ADMIN' && retake.createdBy !== user.id) {
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
                                    details: { subject: 'Назначена пересдача в системе', type: `Попытка ${r.attemptNumber}`, location: r.link ? 'Онлайн' : (r.roomUuid || 'Очно') }
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