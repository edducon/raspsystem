from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import TeacherLocal
from app.services.raspyx_service import RaspyxService


class ScheduleDataService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.raspyx = RaspyxService()

    def get_dictionaries(self) -> dict:
        groups = [
            {
                "uuid": str(item.get("uuid") or ""),
                "number": str(item.get("number") or ""),
            }
            for item in self._result_items(self.raspyx.get_groups())
            if item.get("uuid") and item.get("number")
        ]
        subjects = [
            {
                "uuid": str(item.get("uuid") or ""),
                "name": str(item.get("name") or ""),
            }
            for item in self._result_items(self.raspyx.get_subjects())
            if item.get("uuid") and item.get("name")
        ]

        groups.sort(key=lambda item: item["number"])
        subjects.sort(key=lambda item: item["name"])
        return {"groups": groups, "subjects": subjects}

    def get_teacher_schedule(self, teacher_uuid: str) -> dict:
        teacher = self.db.get(TeacherLocal, teacher_uuid)
        if teacher is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher directory entry not found",
            )

        payload = self.raspyx.get_teacher_schedule(teacher.full_name)
        return {
            "teacher_uuid": teacher.uuid,
            "teacher_full_name": teacher.full_name,
            "schedule": self._schedule_root(payload),
        }

    def _result_items(self, payload: object) -> list[dict]:
        if not isinstance(payload, dict):
            return []
        result = payload.get("result") or payload.get("response") or []
        return result if isinstance(result, list) else []

    def _schedule_root(self, payload: object) -> dict[str, object]:
        if not isinstance(payload, dict):
            return {}
        root = payload.get("result") or payload.get("response") or {}
        return root if isinstance(root, dict) else {}
