import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import ScheduleSnapshot
from app.services.schedule_snapshot_service import ScheduleSnapshotService

MOSCOW_TZ = timezone(timedelta(hours=3))

def check_and_sync_schedule():
    """Синхронная функция: проверяет календарь и запускает синхронизацию"""
    db = SessionLocal()
    try:
        today = datetime.now(MOSCOW_TZ).date()

        # 1. Проверяем, старт ли это нового семестра (9 февраля или 1 сентября)
        is_semester_start = (today.month == 2 and today.day == 9) or (today.month == 9 and today.day == 1)

        # 2. Проверяем, понедельник ли сегодня (weekday() == 0)
        is_monday = today.weekday() == 0

        if is_semester_start:
            print(f"[Auto-Sync] Наступило {today}. Старт нового семестра! Запускаем полную синхронизацию...")
            service = ScheduleSnapshotService(db)
            service.sync_from_raspyx()
            print("[Auto-Sync] Новый семестр успешно создан и назначен эталоном.")

        elif is_monday:
            # Понедельник: обновляем расписание, только если уже есть активный семестр
            active_snapshot = db.scalar(
                select(ScheduleSnapshot)
                .where(ScheduleSnapshot.is_reference_for_retakes.is_(True))
            )
            if active_snapshot:
                print(f"[Auto-Sync] Сегодня понедельник ({today}). Проверяем обновления расписания...")
                service = ScheduleSnapshotService(db)
                # sync_from_raspyx заархивирует текущий и создаст свежий с тем же лейблом
                service.sync_from_raspyx()
                print("[Auto-Sync] Еженедельное обновление расписания завершено.")
            else:
                print("[Auto-Sync] Понедельник, но активного семестра нет. Ждем старта семестра.")

        else:
            print(f"[Auto-Sync] Сегодня {today}. Не старт семестра и не понедельник. Спим дальше.")

    except Exception as e:
        print(f"[Auto-Sync] Ошибка при автоматической синхронизации: {e}")
        db.rollback()
    finally:
        db.close()


async def auto_archive_loop():
    """Асинхронный цикл, просыпается каждую ночь в 03:00"""
    while True:
        # 1. Запускаем логику проверки и синхронизации
        await asyncio.to_thread(check_and_sync_schedule)

        # 2. Высчитываем время до следующих 03:00 ночи (UTC)
        now = datetime.now(MOSCOW_TZ)
        next_run = now.replace(hour=3, minute=0, second=0, microsecond=0)

        # Если 3 часа ночи сегодня уже прошло, переносим на завтра
        if now >= next_run:
            next_run += timedelta(days=1)

        # Считаем разницу в секундах
        sleep_seconds = (next_run - now).total_seconds()

        print(f"[Auto-Sync] Следующая проверка запланирована через {sleep_seconds / 3600:.1f} часов")

        # 3. Засыпаем ровно до этого времени
        await asyncio.sleep(sleep_seconds)