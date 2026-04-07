from __future__ import annotations

import argparse
import sys

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import User


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create the first admin user.")
    parser.add_argument("--username", required=True, help="Login for the admin user.")
    parser.add_argument("--password", required=True, help="Temporary password for the admin user.")
    parser.add_argument("--full-name", required=True, dest="full_name", help="Full name to display in the UI.")
    parser.add_argument("--department-id", type=int, default=None, dest="department_id", help="Optional department id.")
    parser.add_argument(
        "--no-force-password-change",
        action="store_true",
        help="Do not require password change on first login.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    session = SessionLocal()

    try:
        existing_user = session.query(User).filter(User.username == args.username).first()
        if existing_user is not None:
            print(f"User '{args.username}' already exists.", file=sys.stderr)
            return 1

        department_ids = [args.department_id] if args.department_id is not None else []
        admin = User(
            username=args.username,
            full_name=args.full_name,
            password_hash=hash_password(args.password),
            role="ADMIN",
            is_active=True,
            session_version=1,
            must_change_password=not args.no_force_password_change,
            department_id=args.department_id,
            department_ids=department_ids,
            teacher_uuid=None,
        )
        session.add(admin)
        session.commit()
        session.refresh(admin)
    finally:
        session.close()

    print(f"Created admin user '{args.username}' (id={admin.id}).")
    if admin.must_change_password:
        print("The user must change the password on first login.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
