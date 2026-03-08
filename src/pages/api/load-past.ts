export const prerender = false;

import type { APIRoute } from 'astro';
import { db } from '../../db';
import { pastSemester } from '../../db/schema';
import fs from 'node:fs/promises';
import path from 'node:path';

export const GET: APIRoute = async () => {
    try {
        // 1. Читаем файл из корня проекта
        const filePath = path.resolve(process.cwd(), 'schedules.json');
        const fileContent = await fs.readFile(filePath, 'utf-8');
        const jsonData = JSON.parse(fileContent);

        if (jsonData.status !== "OK" || !jsonData.response) {
            throw new Error("Неверный формат файла schedules.json");
        }

        const recordsMap = new Map<string, Set<string>>();

        // Проходим по всем датам
        for (const date in jsonData.response) {
            const daySchedule = jsonData.response[date];

            // Проходим по всем парам (1-7)
            for (const slot in daySchedule) {
                const pairs = daySchedule[slot];

                if (Array.isArray(pairs)) {
                    for (const pair of pairs) {
                        // Формируем уникальный ключ "Группа|Предмет"
                        const key = `${pair.group}|${pair.subject}`;

                        if (!recordsMap.has(key)) {
                            recordsMap.set(key, new Set());
                        }

                        // Добавляем всех преподавателей (Set гарантирует уникальность)
                        if (Array.isArray(pair.teachers)) {
                            pair.teachers.forEach((t: string) => recordsMap.get(key)!.add(t));
                        }
                    }
                }
            }
        }

        // 3. Подготавливаем массив для вставки в БД
        const insertData = [];
        for (const [key, teachersSet] of recordsMap.entries()) {
            const [groupName, subjectName] = key.split('|');
            insertData.push({
                groupName,
                subjectName,
                teacherNames: Array.from(teachersSet) // Преобразуем Set обратно в массив
            });
        }

        // 4. Очищаем старые данные (если скрипт запускается повторно)
        // и заливаем новые батчами
        await db.delete(pastSemester);

        if (insertData.length > 0) {
            await db.insert(pastSemester).values(insertData);
        }

        return new Response(JSON.stringify({
            success: true,
            message: `Успешно загружено ${insertData.length} уникальных связок (группа-предмет).`
        }), { status: 200, headers: { 'Content-Type': 'application/json' }});

    } catch (error: any) {
        console.error("Ошибка при обработке JSON:", error);
        return new Response(JSON.stringify({ success: false, error: error.message }), {
            status: 500, headers: { 'Content-Type': 'application/json' }
        });
    }
};