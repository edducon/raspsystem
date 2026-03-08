export const prerender = false;

import type { APIRoute } from 'astro';
import { db } from '../../db';
import { users, departments, teachersLocal } from '../../db/schema';
import { Argon2id } from 'oslo/password'; // Безопасное хеширование паролей
import { RaspyxAPI } from '../../lib/api-client';

export const GET: APIRoute = async () => {
    try {
        // 1. Создаем тестовую кафедру (потом через админку добавишь остальные)
        const [dept] = await db.insert(departments).values({
            name: "Информационные технологии"
        }).returning();

        // 2. Создаем первого администратора
        // Генерируем хэш пароля (пароль будет: admin123)
        const hashedPassword = await new Argon2id().hash("admin123");

        await db.insert(users).values({
            id: "user_admin_001", // Для Lucia ID должен быть строкой
            username: "admin",
            passwordHash: hashedPassword,
            role: "ADMIN",
            departmentId: dept.id
        }).onConflictDoNothing(); // Игнорируем ошибку, если админ уже существует

        // 3. Парсим преподавателей из API
        // Вытягиваем реальных преподов
        const teachersResponse = await RaspyxAPI.getTeachers();

        // Если API вернуло массив в result
        if (teachersResponse && teachersResponse.result) {
            // Подготавливаем данные под нашу схему БД
            const teachersToInsert = teachersResponse.result.map((t: any) => ({
                uuid: t.uuid,
                fullName: t.full_name,
                departmentId: null // Временно всех кидаем на одну кафедру
            }));

            // Массово добавляем в локальную БД
            if (teachersToInsert.length > 0) {
                await db.insert(teachersLocal).values(teachersToInsert).onConflictDoNothing();
            }
        }

        return new Response(JSON.stringify({
            success: true,
            message: "База данных успешно инициализирована! Админ создан, преподаватели загружены."
        }), {
            status: 200,
            headers: { 'Content-Type': 'application/json' }
        });

    } catch (error: any) {
        console.error("Ошибка при заполнении БД:", error);
        return new Response(JSON.stringify({ success: false, error: error.message }), {
            status: 500,
            headers: { 'Content-Type': 'application/json' }
        });
    }
};