from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.core.security import get_current_user, require_role
from app.models import User, Student, Class, TransferHistory, Attendance
from app.schemas import LogEntry

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("/records", response_model=List[LogEntry])
def list_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("school_admin", "secretary", "staff", module="logs")),
):
    results = []

    # Transferências da escola do usuário
    transfers = (
        db.query(TransferHistory)
        .join(Student, TransferHistory.student_id == Student.id)
        .filter(Student.school_id == current_user.school_id)
        .order_by(TransferHistory.transferred_at.desc())
        .all()
    )

    for t in transfers:
        student = db.query(Student).filter(Student.id == t.student_id).first()
        from_class = db.query(Class).filter(Class.id == t.from_class_id).first() if t.from_class_id else None
        to_class = db.query(Class).filter(Class.id == t.to_class_id).first() if t.to_class_id else None
        user = db.query(User).filter(User.id == t.registered_by_user_id).first() if t.registered_by_user_id else None

        results.append(LogEntry(
            id=t.id,
            type="transferência",
            student_id=t.student_id,
            student_name=student.full_name if student else "-",
            date=None,
            from_class_name=from_class.name if from_class else ("Externa" if t.transfer_type == "external" else "-"),
            to_class_name=to_class.name if to_class else ("Externa" if t.transfer_type == "external" else "-"),
            reason=t.reason or "-",
            registered_by_name=user.full_name if user else "-",
            registered_at=t.transferred_at,
        ))

    # Justificativas de faltas da escola do usuário
    justifications = (
        db.query(Attendance)
        .join(Student, Attendance.student_id == Student.id)
        .filter(
            Student.school_id == current_user.school_id,
            Attendance.status == "justified",
            Attendance.justification.isnot(None),
        )
        .order_by(Attendance.registered_at.desc())
        .all()
    )

    for j in justifications:
        student = db.query(Student).filter(Student.id == j.student_id).first()
        user = db.query(User).filter(User.id == j.registered_by_user_id).first() if j.registered_by_user_id else None

        results.append(LogEntry(
            id=j.id,
            type="justificativa",
            student_id=j.student_id,
            student_name=student.full_name if student else "-",
            date=j.date,
            from_class_name=None,
            to_class_name=None,
            reason=j.justification or "-",
            registered_by_name=user.full_name if user else "-",
            registered_at=j.registered_at,
        ))

    # Ordena por data/hora decrescente
    results.sort(key=lambda x: x.registered_at, reverse=True)
    return results
