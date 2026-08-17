from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date, datetime, time

from app.db.session import get_db
from app.core.security import get_current_user, require_role
from app.models import User, Attendance, Student, Shift
from app.schemas import AttendanceCreate, AttendanceResponse, JustifyAbsenceRequest
from app.services.qr_service import decrypt_qr_payload
from app.core.module_guard import require_module_for_current_school

router = APIRouter(prefix="/attendance", tags=["attendance"])


def _parse_time(value: str):
    try:
        return time(*map(int, value.split(":")))
    except Exception:
        return None


def _check_shift_window(shift: Shift):
    now = datetime.now()
    start = _parse_time(shift.start_time) if shift.start_time else None
    end = _parse_time(shift.end_time) if shift.end_time else None

    if start and end:
        if start < end:
            in_window = start <= now.time() <= end
        else:
            # turno cruza a meia-noite
            in_window = now.time() >= start or now.time() <= end
    elif end:
        in_window = now.time() <= end
    elif start:
        in_window = now.time() >= start
    else:
        return

    if not in_window:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Leitura fora do horário do turno {shift.name} ({shift.start_time or '--:--'} às {shift.end_time or '--:--'})"
        )


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

    today = date.today().isoformat()
    is_temporary = qr_data.get("tmp") is True

    if not is_temporary:
        # Validação do ano letivo: a carteirinha normal só vale para o ano da turma em que foi gerada.
        current_year = student.class_.year if student.class_ else date.today().year
        qr_year = qr_data.get("year")
        if qr_year is not None and qr_year != current_year:
            raise HTTPException(status_code=403, detail="Carteirinha inválida — ano letivo expirado")

    if is_temporary:
        qr_date = qr_data.get("date") or qr_data.get("d")
        if qr_date != today:
            raise HTTPException(status_code=403, detail="Carteirinha provisória expirada — data inválida")

        expires_at_str = qr_data.get("exp") or qr_data.get("e")
        if not expires_at_str:
            raise HTTPException(status_code=400, detail="Carteirinha provisória sem validade")
        try:
            expires_at = datetime.fromisoformat(expires_at_str)
        except Exception:
            raise HTTPException(status_code=400, detail="Carteirinha provisória com validade inválida")
        if datetime.now() > expires_at:
            raise HTTPException(status_code=403, detail="Carteirinha provisória expirada — turno encerrado")

        shift_id = qr_data.get("shift") or qr_data.get("s")
        if not shift_id:
            raise HTTPException(status_code=400, detail="Carteirinha provisória sem turno")
    else:
        shift_id = payload.shift_id

    shift = db.query(Shift).filter(Shift.id == shift_id, Shift.school_id == current_user.school_id).first()
    if not shift:
        raise HTTPException(status_code=404, detail="Turno não encontrado")

    _check_shift_window(shift)

    existing = db.query(Attendance).filter(
        Attendance.student_id == student.id,
        Attendance.shift_id == shift.id,
        Attendance.date == today,
    ).first()

    if existing:
        if existing.status == "present":
            raise HTTPException(status_code=409, detail="Presença já registrada para este aluno hoje neste turno")
        # Se o scheduler criou uma falta automática, atualiza para presente no QR scan.
        existing.status = "present"
        existing.registered_by_user_id = current_user.id
        db.commit()
        db.refresh(existing)
        return existing

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
