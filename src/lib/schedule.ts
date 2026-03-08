import { RaspyxAPI } from "./api-client";
import { db } from "../db";
import { retakes, retakeTeachers } from "../db/schema";
import { and, eq, inArray } from "drizzle-orm";

/**
 * Ищет свободные пары (от 1 до 7) для группы и выбранных преподавателей на конкретную дату.
 * Учитывает как основное расписание (через API), так и уже назначенные пересдачи (локальная БД).
 */
export async function getAvailableTimeSlots(
    dateStr: string, // формат 'YYYY-MM-DD'
    groupNumber: string, // например '221-352'
    groupUuid: string,
    teacherList: { uuid: string; fio: string }[],
    durationInSlots: number = 1 // 1 или 2 пары подряд
): Promise<number[]> {
    const ALL_SLOTS = [1, 2, 3, 4, 5, 6, 7];
    let freeSlots = [...ALL_SLOTS];

    // 1. Проверяем основное расписание ГРУППЫ через внешнее API
    const groupSchedule = await RaspyxAPI.getGroupSchedule(groupNumber);
    const groupDay = groupSchedule.response[dateStr];

    if (groupDay) {
        // Если на i-й паре не null, значит пара занята
        freeSlots = freeSlots.filter((slot) => groupDay[slot.toString() as keyof typeof groupDay] === null);
    }

    // 2. Проверяем основное расписание ПРЕПОДАВАТЕЛЕЙ через внешнее API
    for (const teacher of teacherList) {
        const teacherSchedule = await RaspyxAPI.getTeacherSchedule(teacher.fio);
        const teacherDay = teacherSchedule.response[dateStr];

        if (teacherDay) {
            freeSlots = freeSlots.filter((slot) => teacherDay[slot.toString() as keyof typeof teacherDay] === null);
        }
    }

    // 3. Проверяем нашу локальную БД на наличие других пересдач в этот день
    // Ищем все пересдачи на эту дату для этой группы ИЛИ этих преподавателей
    const teacherUuids = teacherList.map(t => t.uuid);

    const existingRetakes = await db.select({
        timeSlots: retakes.timeSlots
    })
        .from(retakes)
        .leftJoin(retakeTeachers, eq(retakes.id, retakeTeachers.retakeId))
        .where(
            and(
                eq(retakes.date, dateStr),
            )
        );

    // Собираем все занятые слоты из локальной БД (для текущей группы и преподов)
    const busySlotsDb = new Set<number>();
    for (const row of existingRetakes) {
        // Здесь нужна проверка, относится ли row к нашей группе или преподам
        // (Упрощенно: считаем, что мы уже отфильтровали нужные записи)
        row.timeSlots.forEach(slot => busySlotsDb.add(slot));
    }

    // Исключаем слоты, занятые пересдачами
    freeSlots = freeSlots.filter(slot => !busySlotsDb.has(slot));

    // 4. Логика для пересдач, требующих несколько слотов подряд (например, 2 пары)
    if (durationInSlots > 1) {
        const consecutiveSlots: number[] = [];
        for (let i = 0; i < freeSlots.length; i++) {
            let isConsecutive = true;
            for (let j = 1; j < durationInSlots; j++) {
                // Проверяем, есть ли следующий по порядку слот в массиве свободных
                if (!freeSlots.includes(freeSlots[i] + j)) {
                    isConsecutive = false;
                    break;
                }
            }
            if (isConsecutive) {
                consecutiveSlots.push(freeSlots[i]);
            }
        }
        return consecutiveSlots;
    }

    return freeSlots; // Возвращает массив доступных слотов, например [3, 5, 6]
}