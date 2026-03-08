import type { APIRoute } from 'astro';
import { db } from '../../db';
import { retakes, retakeTeachers } from '../../db/schema';

export const GET: APIRoute = async () => {
    try {
        // Сначала удаляем связи (преподавателей на пересдачах)
        await db.delete(retakeTeachers);
        // Затем удаляем сами пересдачи
        await db.delete(retakes);

        return new Response(JSON.stringify({
            success: true,
            message: "БД успешно очищена! Все пересдачи удалены."
        }), {
            status: 200,
            headers: { 'Content-Type': 'application/json' }
        });
    } catch (e: any) {
        return new Response(JSON.stringify({
            success: false,
            error: e.message
        }), { status: 500 });
    }
};