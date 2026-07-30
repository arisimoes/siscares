from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date, datetime

from app.db.session import get_db
from app.core.security import get_current_user, require_role
from app.models import User, Attendance, Student, Shift
from app.schemas import AttendanceCreate, AttendanceResponse, JustifyAbsenceRequest
from app.services.qr_service import decrypt_qr_payload
from app.core.module_guard import require_module_for_current_school

router = APIRouter(prefix="/attendance", tags=["attendance"])


def _check_attendance_window():
    hour = datetime.now().hour
    if hour < 6 or hour >= 22:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Leitura de QR Code permitida apenas entre 6h e 22h")


@router.post("", response_model=AttendanceResponse)
def register_attendance(
    payload: AttendanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("super_admin", "school_admin", "secretary", "staff", module="attendance")),
):
    require_module_for_current_school(db, current_user, "attendance")
    _check_attendance_window()

    try:
        qr_data = decrypt_qr_payload(payload.qr_payload)
    except Exception:
        raise HTTPException(status_code=400, detail="QR Code inválido ou corrompido")

    student_id = qr_data.get("sid")
    if not student_id:
        raise HTTPException(status_code=400, detail="QR Code não contém identificação do aluno")
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")
    if student.school_id != current_user.school_id:
        raise HTTPException(status_code=404, detail="Aluno não pertence à escola")
    if not student.is_active:
        raise HTTPException(status_code=403, detail="Aluno inativo — matrícula cancelada")
    if student.is_transferred_externally:
        raise HTTPException(status_code=403, detail="Carteirinha inválida — aluno transferido externamente")

    shift = db.query(Shift).filter(Shift.id == payload.shift_id, Shift.school_id == current_user.school_id).first()
    if not shift:
        raise HTTPException(status_code=404, detail="Turno não encontrado")

    today = date.today().isoformat()
    existing = db.query(Attendance).filter(
        Attendance.student_id == student.id,
        Attendance.shift_id == shift.id,
        Attendance.date == today,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Presença já registrada para este aluno hoje neste turno")

    attendance = Attendance(
        student_id=student.id,
        shift_id=shift.id,
        date=today,
        status="present",
        registered_by_user_id=current_user.id,
    )
    db.add(attendance)
    db.commit()
    db.refresh(attendance)
    return attendance


@router.post("/justify/{student_id}", response_model=AttendanceResponse)
def justify_absence(
    student_id: int,
    payload: JustifyAbsenceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("super_admin", "school_admin", "secretary", "staff", module="attendance")),
):
    require_module_for_current_school(db, current_user, "attendance")

    student = db.query(Student).filter(Student.id == student_id, Student.school_id == current_user.school_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")

    attendance = db.query(Attendance).filter(
        Attendance.student_id == student_id,
        Attendance.date == payload.date,
        Attendance.status == "absent",
    ).order_by(Attendance.id).first()

    if not attendance:
        raise HTTPException(status_code=404, detail="Nenhuma falta encontrada para este aluno na data informada")

    attendance.status = "justified"
    attendance.justification = payload.justification
    attendance.registered_by_user_id = current_user.id
    db.commit()
    db.refresh(attendance)
    return attendance
