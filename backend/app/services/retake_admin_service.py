from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import re
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models import PastSemester, Retake, RetakeTeacher
from app.services.raspyx_service import RaspyxService


DATE_VALUE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DATE_HINT_KEYS = {"date", "start_date", "end_date", "startDate", "endDate"}


class RetakeAdminService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.raspyx = RaspyxService()

    def get_past_semester_status(self) -> dict:
        imported_records = int(self.db.scalar(select(func.count()).select_from(PastSemester)) or 0)
        unique_groups = int(self.db.scalar(select(func.count(func.distinct(PastSemester.group_name)))) or 0)
        unique_subjects = int(self.db.scalar(select(func.count(func.distinct(PastSemester.subject_name)))) or 0)

        date_bounds_row = self.db.execute(
            select(
                func.max(PastSemester.date_range_start),
                func.max(PastSemester.date_range_end),
            )
        ).one()
        date_range_start = date_bounds_row[0]
        date_range_end = date_bounds_row[1]

        if imported_records > 0 and (not date_range_start or not date_range_end):
            fallback_start, fallback_end = self._load_default_schedule_date_bounds()
            date_range_start = date_range_start or fallback_start
            date_range_end = date_range_end or fallback_end

        return {
            "is_loaded": imported_records > 0,
            "imported_records": imported_records,
            "unique_groups": unique_groups,
            "unique_subjects": unique_subjects,
            "date_range_start": date_range_start,
            "date_range_end": date_range_end,
        }

    def import_past_semester(self, source_path: str | None = None) -> dict:
        file_path = self._resolve_source_path(source_path)
        payload = self._load_payload(file_path)
        return self._do_import(payload, source_label=str(file_path))

    def import_past_semester_json(self, payload: dict) -> dict:
        return self._do_import(payload, source_label="browser-upload")

    def import_current_semester_as_past(self) -> dict:
        groups_payload = self.raspyx.get_groups()
        groups = self._result_items(groups_payload)
        normalized_groups = list(dict.fromkeys(filter(None, (self._extract_group_number(group) for group in groups))))
        if not groups:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Не удалось получить список групп из API 2.0.0.",
            )
        if not normalized_groups:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="API 2.0.0 вернул список групп без номеров, импорт прошлого семестра невозможен.",
            )

        records_map: dict[tuple[str, str], set[str]] = {}
        collected_payloads: list[object] = []
        processed_groups = 0
        failed_group_numbers: list[str] = []
        max_workers = min(8, len(normalized_groups))

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_group = {
                executor.submit(self.raspyx.get_group_schedule, group_number): group_number
                for group_number in normalized_groups
            }

            for future in as_completed(future_to_group):
                group_number = future_to_group[future]
                try:
                    schedule_payload = future.result()
                except Exception:
                    failed_group_numbers.append(group_number)
                    continue

                collected_payloads.append(schedule_payload)
                schedule_root = self._schedule_root(schedule_payload)
                if not schedule_root:
                    failed_group_numbers.append(group_number)
                    continue

                processed_groups += 1
                self._collect_schedule_pairs(schedule_root, records_map, fallback_group_name=group_number)

        if not records_map:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Не удалось собрать локальные данные прошлого семестра из текущего API 2.0.0. Все запросы по группам завершились пустым ответом или таймаутом.",
            )

        date_range_start, date_range_end = self._extract_date_bounds(collected_payloads)
        rows = [
            PastSemester(
                group_name=group_name,
                subject_name=subject_name,
                teacher_names=sorted(teacher_names),
                date_range_start=date_range_start,
                date_range_end=date_range_end,
            )
            for (group_name, subject_name), teacher_names in sorted(records_map.items())
        ]

        self.db.execute(delete(PastSemester))
        if rows:
            self.db.add_all(rows)
        self.db.commit()

        total_groups = len(normalized_groups)
        skipped_groups = len(failed_group_numbers)
        message_parts = [
            "Текущий семестр из API 2.0.0 сохранён как прошлый.",
            f"Успешно обработано групп: {processed_groups} из {total_groups}.",
            f"Записей: {len(rows)}.",
        ]
        if skipped_groups:
            message_parts.append(f"Пропущено из-за пустого ответа или таймаута: {skipped_groups}.")

        return {
            "success": True,
            "source_path": "api-v2-current-semester",
            "imported_records": len(rows),
            "unique_groups": len({row.group_name for row in rows}),
            "unique_subjects": len({row.subject_name for row in rows}),
            "date_range_start": date_range_start,
            "date_range_end": date_range_end,
            "message": " ".join(message_parts),
        }
        if not groups:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Не удалось получить список групп из API 2.0.0.",
            )

        records_map: dict[tuple[str, str], set[str]] = {}
        collected_payloads: list[object] = []
        processed_groups = 0

        for group in groups:
            group_number = self._extract_group_number(group)
            if not group_number:
                continue

            schedule_payload = self.raspyx.get_group_schedule(group_number)
            collected_payloads.append(schedule_payload)
            schedule_root = self._schedule_root(schedule_payload)
            if not schedule_root:
                continue

            processed_groups += 1
            self._collect_schedule_pairs(schedule_root, records_map, fallback_group_name=group_number)

        if not records_map:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Не удалось собрать локальные данные прошлого семестра из текущего API 2.0.0.",
            )

        date_range_start, date_range_end = self._extract_date_bounds(collected_payloads)
        rows = [
            PastSemester(
                group_name=group_name,
                subject_name=subject_name,
                teacher_names=sorted(teacher_names),
                date_range_start=date_range_start,
                date_range_end=date_range_end,
            )
            for (group_name, subject_name), teacher_names in sorted(records_map.items())
        ]

        self.db.execute(delete(PastSemester))
        if rows:
            self.db.add_all(rows)
        self.db.commit()

        return {
            "success": True,
            "source_path": "api-v2-current-semester",
            "imported_records": len(rows),
            "unique_groups": len({row.group_name for row in rows}),
            "unique_subjects": len({row.subject_name for row in rows}),
            "date_range_start": date_range_start,
            "date_range_end": date_range_end,
            "message": f"Текущий семестр из API 2.0.0 сохранён как прошлый. Обработано групп: {processed_groups}, записей: {len(rows)}.",
        }

    def _do_import(self, payload: dict, source_label: str) -> dict:
        raw_schedule = payload.get("response")
        if payload.get("status") != "OK" or not isinstance(raw_schedule, dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Файл имеет некорректный формат. Ожидается {"status": "OK", "response": {...}}.',
            )

        date_range_start, date_range_end = self._extract_date_bounds(payload)
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
                date_range_start=date_range_start,
                date_range_end=date_range_end,
            )
            for (group_name, subject_name), teacher_names in sorted(records_map.items())
        ]

        self.db.execute(delete(PastSemester))
        if rows:
            self.db.add_all(rows)
        self.db.commit()

        return {
            "success": True,
            "source_path": source_label,
            "imported_records": len(rows),
            "unique_groups": len({row.group_name for row in rows}),
            "unique_subjects": len({row.subject_name for row in rows}),
            "date_range_start": date_range_start,
            "date_range_end": date_range_end,
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
            detail=f"Файл не найден. Проверены пути: {', '.join(checked_paths)}.",
        )

    def _load_payload(self, file_path: Path) -> dict:
        try:
            return json.loads(file_path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Файл не найден: {file_path}.",
            ) from exc
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Некорректный JSON: {exc}.",
            ) from exc

    def _load_default_schedule_date_bounds(self) -> tuple[str | None, str | None]:
        try:
            file_path = self._resolve_source_path(None)
            payload = self._load_payload(file_path)
        except HTTPException:
            return None, None
        return self._extract_date_bounds(payload)

    def _extract_date_bounds(self, payload: object) -> tuple[str | None, str | None]:
        collected: set[str] = set()
        self._collect_dates(payload, collected)
        if not collected:
            return None, None
        ordered = sorted(collected)
        return ordered[0], ordered[-1]

    def _result_items(self, payload: object) -> list[dict]:
        if not isinstance(payload, dict):
            return []
        result = payload.get("result") or payload.get("response") or []
        return result if isinstance(result, list) else []

    def _schedule_root(self, payload: object) -> dict:
        if not isinstance(payload, dict):
            return {}
        result = payload.get("result") or payload.get("response") or {}
        return result if isinstance(result, dict) else {}

    def _extract_group_number(self, group: object) -> str:
        if not isinstance(group, dict):
            return ""
        return str(group.get("number") or group.get("group_number") or group.get("name") or "").strip()

    def _extract_pair_group_name(self, pair: dict, fallback_group_name: str) -> str:
        group = pair.get("group")
        if isinstance(group, dict):
            candidate = str(group.get("number") or group.get("name") or "").strip()
            if candidate:
                return candidate
        if isinstance(group, str) and group.strip():
            return group.strip()
        return fallback_group_name

    def _extract_pair_subject_name(self, pair: dict) -> str:
        subject = pair.get("subject")
        if isinstance(subject, dict):
            candidate = str(subject.get("name") or subject.get("subject_name") or "").strip()
            if candidate:
                return candidate
        if isinstance(subject, str) and subject.strip():
            return subject.strip()
        return str(pair.get("subject_name") or "").strip()

    def _extract_pair_teacher_name(self, teacher: object) -> str:
        if isinstance(teacher, str):
            return teacher.strip()
        if not isinstance(teacher, dict):
            return ""

        for key in ("full_name", "fio", "teacher_fio", "name"):
            candidate = str(teacher.get(key) or "").strip()
            if candidate:
                return candidate
        return ""

    def _collect_schedule_pairs(
        self,
        schedule_root: dict,
        records_map: dict[tuple[str, str], set[str]],
        *,
        fallback_group_name: str,
    ) -> None:
        for day_schedule in schedule_root.values():
            if not isinstance(day_schedule, dict):
                continue

            for pairs in day_schedule.values():
                if not isinstance(pairs, list):
                    continue

                for pair in pairs:
                    if not isinstance(pair, dict):
                        continue

                    group_name = self._extract_pair_group_name(pair, fallback_group_name=fallback_group_name)
                    subject_name = self._extract_pair_subject_name(pair)
                    if not group_name or not subject_name:
                        continue

                    teachers = records_map.setdefault((group_name, subject_name), set())
                    for teacher in pair.get("teachers") or []:
                        teacher_name = self._extract_pair_teacher_name(teacher)
                        if teacher_name:
                            teachers.add(teacher_name)

    def _collect_dates(self, value: object, sink: set[str]) -> None:
        if isinstance(value, str):
            if DATE_VALUE_RE.fullmatch(value.strip()):
                sink.add(value.strip())
            return

        if isinstance(value, list):
            for item in value:
                self._collect_dates(item, sink)
            return

        if not isinstance(value, dict):
            return

        for key, nested_value in value.items():
            key_str = str(key).strip()
            if DATE_VALUE_RE.fullmatch(key_str):
                sink.add(key_str)

            if key_str in DATE_HINT_KEYS and isinstance(nested_value, str) and DATE_VALUE_RE.fullmatch(nested_value.strip()):
                sink.add(nested_value.strip())

            self._collect_dates(nested_value, sink)
