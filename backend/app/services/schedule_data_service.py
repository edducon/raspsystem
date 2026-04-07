from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import TeacherLocal, User
from app.services.reference_schedule_service import ReferenceScheduleService
from app.services.raspyx_service import RaspyxService


class ScheduleDataService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.raspyx = RaspyxService()
        self.reference_schedule = ReferenceScheduleService(db)

    def get_dictionaries(self) -> dict:
        if self.reference_schedule.has_reference_snapshot():
            groups = self._normalize_groups(self.reference_schedule.list_groups())
            subjects = [
                {
                    "uuid": str(item.get("uuid") or ""),
                    "name": str(item.get("name") or ""),
                }
                for item in self.reference_schedule.list_subjects()
                if item.get("uuid") and item.get("name")
            ]
            groups.sort(key=lambda item: item["number"])
            subjects.sort(key=lambda item: item["name"])
            return {"groups": groups, "subjects": subjects}

        groups = self._normalize_groups(self._result_items(self.raspyx.get_groups()))
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

    def get_teacher_schedule(self, teacher_uuid: str, viewer: User) -> dict:
        teacher = self.db.get(TeacherLocal, teacher_uuid)
        if teacher is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="РџСЂРµРїРѕРґР°РІР°С‚РµР»СЊ РёР· СЃРїСЂР°РІРѕС‡РЅРёРєР° РЅРµ РЅР°Р№РґРµРЅ.",
            )

        if viewer.role != "ADMIN" and viewer.teacher_uuid != teacher_uuid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Р”РѕСЃС‚СѓРї Рє СЂР°СЃРїРёСЃР°РЅРёСЋ СЂР°Р·СЂРµС€С‘РЅ С‚РѕР»СЊРєРѕ РґР»СЏ СЃРѕР±СЃС‚РІРµРЅРЅРѕР№ СѓС‡С‘С‚РЅРѕР№ Р·Р°РїРёСЃРё.",
            )

        schedule = (
            self.reference_schedule.build_teacher_schedule_root(teacher.full_name)
            if self.reference_schedule.has_reference_snapshot()
            else self._schedule_root(self.raspyx.get_teacher_schedule(teacher.full_name))
        )
        return {
            "teacher_uuid": teacher.uuid,
            "teacher_full_name": teacher.full_name,
            "schedule": schedule,
        }

    def _result_items(self, payload: object) -> list[dict]:
        if not isinstance(payload, dict):
            return []
        result = payload.get("result") or payload.get("response") or []
        return result if isinstance(result, list) else []

    def _normalize_groups(self, raw_groups: list[dict]) -> list[dict[str, str]]:
        normalized: list[dict[str, str]] = []
        seen_uuids: set[str] = set()

        for item in raw_groups:
            uuid = str(item.get("uuid") or "").strip()
            number = self._extract_group_number(item)
            if not uuid or not number or uuid in seen_uuids:
                continue

            normalized.append({"uuid": uuid, "number": number})
            seen_uuids.add(uuid)

        normalized.sort(key=lambda item: item["number"])
        return normalized

    def _extract_group_number(self, group: object) -> str:
        if not isinstance(group, dict):
            return ""

        for key in ("number", "group_number", "name"):
            candidate = str(group.get(key) or "").strip()
            if candidate:
                return candidate
        return ""

    def _schedule_root(self, payload: object) -> dict[str, object]:
        if not isinstance(payload, dict):
            return {}
        root = payload.get("result") or payload.get("response") or {}
        return root if isinstance(root, dict) else {}
