from __future__ import annotations

import json
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models import PastSemester, Retake, RetakeTeacher


class RetakeAdminService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def import_past_semester(self, source_path: str | None = None) -> dict:
        file_path = self._resolve_source_path(source_path)
        payload = self._load_payload(file_path)

        raw_schedule = payload.get("response")
        if payload.get("status") != "OK" or not isinstance(raw_schedule, dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Файл schedules.json имеет некорректный формат.",
            )

        records_map: dict[tuple[str, str], set[str]] = {}
        for day_schedule in raw_schedule.values():
            if not isinstance(day_schedule, dict):
                continue

            for pairs in day_schedule.values():
                if not isinstance(pairs, list):
                    continue

                for pair in pairs:
                    if not isinstance(pair, dict):
                        continue

                    group_name = str(pair.get("group") or "").strip()
                    subject_name = str(pair.get("subject") or "").strip()
                    if not group_name or not subject_name:
                        continue

                    key = (group_name, subject_name)
                    teachers = records_map.setdefault(key, set())
                    raw_teachers = pair.get("teachers")
                    if isinstance(raw_teachers, list):
                        for teacher_name in raw_teachers:
                            normalized_name = str(teacher_name).strip()
                            if normalized_name:
                                teachers.add(normalized_name)

        rows = [
            PastSemester(
                group_name=group_name,
                subject_name=subject_name,
                teacher_names=sorted(teacher_names),
            )
            for (group_name, subject_name), teacher_names in sorted(records_map.items())
        ]

        self.db.execute(delete(PastSemester))
        if rows:
            self.db.add_all(rows)
        self.db.commit()

        return {
            "success": True,
            "source_path": str(file_path),
            "imported_records": len(rows),
            "unique_groups": len({row.group_name for row in rows}),
            "unique_subjects": len({row.subject_name for row in rows}),
            "message": f"Импортировано записей за прошлый семестр: {len(rows)}.",
        }

    def reset_retakes(self) -> dict:
        retake_count = int(self.db.scalar(select(func.count()).select_from(Retake)) or 0)
        teacher_link_count = int(self.db.scalar(select(func.count()).select_from(RetakeTeacher)) or 0)

        self.db.execute(delete(RetakeTeacher))
        self.db.execute(delete(Retake))
        self.db.commit()

        return {
            "success": True,
            "deleted_retakes": retake_count,
            "deleted_teacher_links": teacher_link_count,
            "message": "Пересдачи и связи с преподавателями удалены.",
        }

    def _resolve_source_path(self, source_path: str | None) -> Path:
        repo_root = Path(__file__).resolve().parents[3]
        candidates: list[Path] = []

        if source_path:
            raw_path = Path(source_path).expanduser()
            if raw_path.is_absolute():
                candidates.append(raw_path)
            else:
                candidates.append(Path.cwd() / raw_path)
                candidates.append(repo_root / raw_path)
                candidates.append(repo_root / "backend" / raw_path)
        else:
            candidates.extend(
                [
                    Path.cwd() / "schedules.json",
                    repo_root / "schedules.json",
                    repo_root / "backend" / "schedules.json",
                ]
            )

        checked_paths: list[str] = []
        for candidate in candidates:
            resolved = candidate.resolve()
            checked_paths.append(str(resolved))
            if resolved.is_file():
                return resolved

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Файл данных за прошлый семестр не найден. Проверены пути: {', '.join(checked_paths)}.",
        )

    def _load_payload(self, file_path: Path) -> dict:
        try:
            return json.loads(file_path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Файл данных за прошлый семестр не найден: {file_path}.",
            ) from exc
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Файл данных за прошлый семестр содержит некорректный JSON: {exc}.",
            ) from exc
