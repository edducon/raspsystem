from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import TeacherLocal
from app.services.raspyx_service import RaspyxService


class TeacherSyncService:
    """Синхронизация преподавателей из Raspyx API (GET /v2/teachers) в локальный справочник."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.raspyx = RaspyxService()

    def sync_from_api(self) -> dict:
        """
        Получает список преподавателей из GET /v2/teachers,
        добавляет отсутствующих в teachers_local по uuid.
        """
        payload = self.raspyx.get_teachers()
        api_teachers = self._result_items(payload)

        if not api_teachers:
            return {
                "success": False,
                "message": "Не удалось получить список преподавателей из API (пустой ответ или ошибка соединения).",
                "created": 0,
                "skipped": 0,
                "total_found": 0,
            }

        existing = list(self.db.scalars(select(TeacherLocal)).all())
        existing_uuids = {t.uuid for t in existing}

        created = 0
        skipped = 0

        for teacher in api_teachers:
            uuid = str(teacher.get("uuid") or "").strip()
            full_name = str(teacher.get("full_name") or "").strip()

            if not uuid or not full_name:
                continue

            if uuid in existing_uuids:
                skipped += 1
                continue

            self.db.add(TeacherLocal(
                uuid=uuid,
                full_name=full_name,
                department_ids=[],
            ))
            existing_uuids.add(uuid)
            created += 1

        if created > 0:
            self.db.commit()

        return {
            "success": True,
            "message": f"Синхронизация завершена. Добавлено: {created}, уже существуют: {skipped}.",
            "created": created,
            "skipped": skipped,
            "total_found": len(api_teachers),
        }

    def _result_items(self, payload: object) -> list[dict]:
        if not isinstance(payload, dict):
            return []
        result = payload.get("result") or payload.get("response") or []
        return result if isinstance(result, list) else []