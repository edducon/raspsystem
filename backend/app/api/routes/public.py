from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/v1/public", tags=["public"])


@router.get("/schedule")
def get_public_schedule(group: str) -> dict[str, str]:
    _ = group
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented yet.")


@router.get("/groups")
def list_public_groups() -> dict[str, str]:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented yet.")


@router.get("/teachers/{teacher_id}/schedule")
def get_public_teacher_schedule(teacher_id: int) -> dict[str, str]:
    _ = teacher_id
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented yet.")
