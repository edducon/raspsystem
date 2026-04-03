from types import SimpleNamespace
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

import app.api.routes.positions as positions_route
import app.api.routes.schedule_snapshots as schedule_snapshots_route
import app.api.routes.teacher_directory as teacher_directory_route
import app.api.routes.users as users_route
from app.api.dependencies.auth import require_admin
from app.db.session import get_db
from app.main import app


def allow_admin():
    return SimpleNamespace(id=1, role="ADMIN", is_active=True)


def deny_admin():
    raise HTTPException(status_code=403, detail="Administrator access required")


class AdminRouteSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        app.dependency_overrides.clear()
        app.dependency_overrides[get_db] = lambda: object()
        app.dependency_overrides[require_admin] = allow_admin
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
        self.assertEqual(response.json()["detail"], "Administrator access required")

    def test_schedule_snapshots_route_is_admin_only(self) -> None:
        app.dependency_overrides[require_admin] = deny_admin

        with patch.object(schedule_snapshots_route.ScheduleSnapshotService, "list_snapshots", return_value=[]):
            response = self.client.get("/api/schedule-snapshots/")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], "Administrator access required")


if __name__ == "__main__":
    unittest.main()
