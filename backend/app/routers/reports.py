from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_user, require_role
from app.models import User
from app.schemas import FrequencyReportResponse
from app.services.report_service import get_frequency_report
from app.core.module_guard import require_module_for_current_school

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/frequency")
def frequency_report(
    month: str,  # YYYY-MM
    class_id: int | None = None,
    day: str | None = None,  # YYYY-MM-DD
    student_name: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("super_admin", "school_admin", "secretary", "staff", module="reports")),
):
    if not current_user.school_id:
        raise HTTPException(status_code=400, detail="Usuário não vinculado a uma escola")
    require_module_for_current_school(db, current_user, "reports")
    return get_frequency_report(
        db,
        current_user.school_id,
        month,
        class_id=class_id,
        day=day,
        student_name=student_name,
    )
