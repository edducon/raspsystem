from datetime import datetime, timezone
from apscheduler.schedulers.blocking import BlockingScheduler
from sqlalchemy import select

from app.db.session import SessionLocal
from app.services.schedule_snapshot_service import ScheduleSnapshotService


def download_semester_job():
    """Задача 1: Тихо качает расписание в конце семестра (20-30 числа)"""
    now = datetime.now(timezone.utc)
    db = SessionLocal()
    try:
        print("[Scheduler] Пытаемся скачать расписание для будущего эталона...")
        service = ScheduleSnapshotService(db)
        result = service.sync_from_raspyx()

        if result:
            print("[Scheduler] Расписание скачано в архив. Ждем начала нового семестра для активации.")
        else:
            print("[Scheduler] Расписание не скачалось или уже существует.")
    except Exception as e:
        print(f"[Scheduler] Ошибка при скачивании: {e}")
    finally:
        db.close()


def activate_reference_job():
    """Задача 2: Делает последний скачанный снимок ЭТАЛОНОМ"""
    print("[Scheduler] СМЕНА СЕМЕСТРА! Активируем новый эталон для пересдач...")
    db = SessionLocal()
    try:
        service = ScheduleSnapshotService(db)
        service.activate_latest_as_reference()
    except Exception as e:
        print(f"[Scheduler] Ошибка при смене эталона: {e}")
    finally:
        db.close()


def start_scheduler():
    scheduler = BlockingScheduler()

    # === НАСТОЯЩИЙ ТАЙМЕР (Боевой режим) ===
    # 1. Тихо качаем расписание в конце семестра (20, 22, 24, 26, 28, 30 числа в 03:00 ночи)
    scheduler.add_job(download_semester_job, 'cron', month='1,7', day='20,22,24,26,28,30', hour=3, minute=0)

    # 2. Делаем последний скачанный снимок эталоном (1 февраля и 1 сентября в 04:00 ночи)
    scheduler.add_job(activate_reference_job, 'cron', month='2,9', day='1', hour=4, minute=0)

    print("[Scheduler] Изолированный Blocking-планировщик запущен.")
    scheduler.start()


if __name__ == "__main__":
    start_scheduler()