from types import SimpleNamespace
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

import app.api.routes.positions as positions_route
import app.api.routes.retakes as retakes_route
import app.api.routes.schedule_snapshots as schedule_snapshots_route
import app.api.routes.teachers as teachers_route
import app.api.routes.teacher_directory as teacher_directory_route
import app.api.routes.users as users_route
from app.api.dependencies.auth import require_admin
from app.api.dependencies.auth import require_scheduler_roles
from app.db.session import get_db
from app.main import app


def allow_admin():
    return SimpleNamespace(id=1, role="ADMIN", is_active=True)


def deny_admin():
    raise HTTPException(status_code=403, detail="Требуются права администратора.")


class AdminRouteSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        app.dependency_overrides.clear()
        app.dependency_overrides[get_db] = lambda: object()
        app.dependency_overrides[require_admin] = allow_admin
        app.dependency_overrides[require_scheduler_roles] = allow_admin
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def test_teacher_directory_create_route(self) -> None:
        with patch.object(
            teacher_directory_route.TeacherDirectoryService,
            "create_teacher",
            return_value={"uuid": "11111111-1111-1111-1111-111111111111", "full_name": "Alice Doe", "department_ids": [1]},
        ) as create_teacher:
            response = self.client.post(
                "/api/teacher-directory/",
                json={"full_name": "Alice Doe", "department_ids": [1]},
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["fullName"], "Alice Doe")
        payload = create_teacher.call_args.args[0]
        self.assertEqual(payload.full_name, "Alice Doe")
        self.assertEqual(payload.department_ids, [1])

    def test_teacher_directory_update_route(self) -> None:
        with patch.object(
            teacher_directory_route.TeacherDirectoryService,
            "update_teacher",
            return_value={"uuid": "11111111-1111-1111-1111-111111111111", "full_name": "Alice Doe", "department_ids": [1, 2]},
        ) as update_teacher:
            response = self.client.put(
                "/api/teacher-directory/11111111-1111-1111-1111-111111111111",
                json={"full_name": "Alice Doe", "department_ids": [1, 2]},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["departmentIds"], [1, 2])
        self.assertEqual(update_teacher.call_args.args[0], "11111111-1111-1111-1111-111111111111")

    def test_teacher_directory_delete_route(self) -> None:
        with patch.object(teacher_directory_route.TeacherDirectoryService, "delete_teacher") as delete_teacher:
            response = self.client.delete("/api/teacher-directory/11111111-1111-1111-1111-111111111111")

        self.assertEqual(response.status_code, 204)
        delete_teacher.assert_called_once_with("11111111-1111-1111-1111-111111111111")

    def test_user_update_accepts_optional_password(self) -> None:
        with patch.object(
            users_route.UserService,
            "update_user",
            return_value={
                "id": 7,
                "username": "admin",
                "full_name": "Admin User",
                "role": "ADMIN",
                "is_active": True,
                "department_id": None,
                "department_ids": [],
                "teacher_uuid": None,
            },
        ) as update_user:
            response = self.client.put(
                "/api/users/7",
                json={
                    "username": "admin",
                    "full_name": "Admin User",
                    "role": "ADMIN",
                    "is_active": True,
                    "department_id": None,
                    "department_ids": [],
                    "teacher_uuid": None,
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = update_user.call_args.args[1]
        self.assertIsNone(payload.password)

    def test_positions_route_is_admin_only(self) -> None:
        app.dependency_overrides[require_admin] = deny_admin

        with patch.object(positions_route.PositionService, "list_positions", return_value=[]):
            response = self.client.get("/api/positions/")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], "Требуются права администратора.")

    def test_schedule_snapshots_route_is_admin_only(self) -> None:
        app.dependency_overrides[require_admin] = deny_admin

        with patch.object(schedule_snapshots_route.ScheduleSnapshotService, "list_snapshots", return_value=[]):
            response = self.client.get("/api/schedule-snapshots/")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], "Требуются права администратора.")

    def test_teacher_create_route(self) -> None:
        with patch.object(
            teachers_route.TeacherService,
            "create_teacher",
            return_value={"id": 3, "full_name": "Иван Иванов", "department_id": 1, "position_id": 2},
        ) as create_teacher:
            response = self.client.post(
                "/api/teachers/",
                json={"full_name": "Иван Иванов", "department_id": 1, "position_id": 2},
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["id"], 3)
        self.assertEqual(response.json()["full_name"], "Иван Иванов")
        payload = create_teacher.call_args.args[0]
        self.assertEqual(payload.full_name, "Иван Иванов")
        self.assertEqual(payload.department_id, 1)
        self.assertEqual(payload.position_id, 2)

    def test_schedule_snapshot_create_route_accepts_contents(self) -> None:
        response_payload = {
            "id": 8,
            "name": "Весна 2026",
            "semester_label": "2025/2026 весна",
            "status": "published",
            "source_type": "manual",
            "description": "Актуальный снимок",
            "is_reference_for_retakes": True,
            "captured_at": "2026-04-03T10:00:00Z",
            "created_at": "2026-04-03T10:00:00Z",
            "groups": [{"uuid": "g-1", "number": "ИВТ-101", "name": "ИВТ-101"}],
            "subjects": [{"uuid": "s-1", "name": "Математика"}],
            "teachers": [{"uuid": "t-1", "full_name": "Иван Иванов", "department_ids": [1]}],
            "schedule_items": [
                {
                    "group_uuid": "g-1",
                    "subject_uuid": "s-1",
                    "teacher_uuids": ["t-1"],
                    "weekday": 1,
                    "slot": 2,
                }
            ],
            "group_count": 1,
            "subject_count": 1,
            "teacher_count": 1,
            "schedule_item_count": 1,
        }
        with patch.object(
            schedule_snapshots_route.ScheduleSnapshotService,
            "create_snapshot",
            return_value=response_payload,
        ) as create_snapshot:
            response = self.client.post(
                "/api/schedule-snapshots/",
                json={
                    "name": "Весна 2026",
                    "semesterLabel": "2025/2026 весна",
                    "status": "published",
                    "sourceType": "manual",
                    "description": "Актуальный снимок",
                    "isReferenceForRetakes": True,
                    "groups": [{"uuid": "g-1", "number": "ИВТ-101", "name": "ИВТ-101"}],
                    "subjects": [{"uuid": "s-1", "name": "Математика"}],
                    "teachers": [{"uuid": "t-1", "fullName": "Иван Иванов", "departmentIds": [1]}],
                    "scheduleItems": [
                        {
                            "groupUuid": "g-1",
                            "subjectUuid": "s-1",
                            "teacherUuids": ["t-1"],
                            "weekday": 1,
                            "slot": 2,
                        }
                    ],
                },
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["groupCount"], 1)
        payload = create_snapshot.call_args.args[0]
        self.assertEqual(payload.semester_label, "2025/2026 весна")
        self.assertEqual(payload.schedule_items[0].group_uuid, "g-1")
        self.assertEqual(payload.teachers[0].full_name, "Иван Иванов")

    def test_retake_form_context_route_uses_backend_payload(self) -> None:
        response_payload = {
            "group_history": [{"subject_name": "Математика", "teacher_names": ["Иван Иванов"]}],
            "existing_retakes": [],
            "available_subjects": [{"uuid": "s-1", "name": "Математика"}],
            "subject_blocked_reason": None,
            "assigned_attempts": [1],
            "next_attempt_number": 2,
            "available_main_teacher_uuids": ["t-1"],
            "available_commission_teacher_uuids": ["t-2"],
            "available_chairman_uuids": ["t-3"],
            "main_teacher_lacks_dept": False,
        }
        with patch.object(
            retakes_route.RetakeService,
            "get_form_context",
            return_value=response_payload,
        ) as get_form_context:
            response = self.client.post(
                "/api/retakes/form-context",
                json={
                    "groupUuid": "g-1",
                    "groupNumber": "ИВТ-101",
                    "subjectUuid": "s-1",
                    "mainTeacherUuids": ["t-1"],
                    "commissionTeacherUuids": ["t-2"],
                    "chairmanUuid": "t-3",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["nextAttemptNumber"], 2)
        payload = get_form_context.call_args.kwargs["payload"]
        self.assertEqual(payload.group_uuid, "g-1")
        self.assertEqual(payload.main_teacher_uuids, ["t-1"])


if __name__ == "__main__":
    unittest.main()
