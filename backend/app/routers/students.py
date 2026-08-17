from datetime import datetime, date, time
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.core.security import get_current_user, require_role
from app.models import User, Student, Class, School, Shift, TemporaryCard
from app.schemas import StudentCreate, StudentResponse, StudentUpdate, StudentDeleteRequest, ClassResponse, TemporaryCardResponse
from app.core.crypto import verify_password
from app.services.qr_service import generate_encrypted_qr_payload, generate_qr_code_base64
import qrcode

router = APIRouter(prefix="/students", tags=["students"])


@router.get("", response_model=List[StudentResponse])
def list_students(
    class_id: int = None,
    shift_id: int = None,
    name: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    results = []
    query = db.query(Student).filter(
        Student.school_id == current_user.school_id,
        Student.is_active == True,
        Student.is_transferred_externally == False,
    )
    if class_id:
        query = query.filter(Student.class_id == class_id)
    if shift_id:
        query = query.join(Class, Student.class_id == Class.id).filter(Class.shift_id == shift_id)
    if name:
        query = query.filter(Student.full_name.ilike(f"%{name}%"))
    for student in query.all():
        data = StudentResponse.model_validate(student)
        row = data.model_dump()
        class_ = db.query(Class).filter(Class.id == student.class_id).first()
        school = db.query(School).filter(School.id == student.school_id).first()
        shift = db.query(Shift).filter(Shift.id == class_.shift_id).first() if class_ else None
        row["class_name"] = f"{class_.name} ({class_.grade})" if class_ else None
        row["shift_name"] = shift.name if shift else None
        row["school_name"] = school.name if school else None
        row["school_photo_url"] = school.photo_url if school else None
        results.append(StudentResponse.model_validate(row))
    return results


@router.post("", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
def create_student(
    payload: StudentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("school_admin", "secretary", "staff", module="students")),
):
    student = Student(school_id=current_user.school_id, **payload.model_dump())
    db.add(student)
    db.commit()
    db.refresh(student)

    student.encrypted_qr_payload = generate_encrypted_qr_payload(student, minimal_payload=True)
    db.commit()
    db.refresh(student)
    return student


@router.get("/{student_id}", response_model=StudentResponse)
def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    student = db.query(Student).filter(Student.id == student_id, Student.school_id == current_user.school_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")
    return student


@router.put("/{student_id}", response_model=StudentResponse)
def update_student(
    student_id: int,
    payload: StudentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("school_admin", "secretary", "staff", module="students")),
):
    student = db.query(Student).filter(Student.id == student_id, Student.school_id == current_user.school_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(student, field, value)
    db.commit()
    db.refresh(student)
    return student


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(
    student_id: int,
    payload: StudentDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("school_admin", "secretary", "staff", module="students")),
):
    student = db.query(Student).filter(Student.id == student_id, Student.school_id == current_user.school_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")
    if not verify_password(payload.password, current_user.hashed_password):
        raise HTTPException(status_code=403, detail="Senha incorreta")
    student.is_active = False
    db.commit()
    return None


@router.get("/{student_id}/qr-text")
def student_qr_text(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    student = db.query(Student).filter(Student.id == student_id, Student.school_id == current_user.school_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")
    if student.is_transferred_externally:
        raise HTTPException(status_code=403, detail="Carteirinha indisponível — aluno transferido externamente")
    if not student.encrypted_qr_payload:
        student.encrypted_qr_payload = generate_encrypted_qr_payload(student, minimal_payload=True)
        db.commit()
    return {"qr_payload": student.encrypted_qr_payload}


@router.get("/{student_id}/card")
def student_card(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    student = db.query(Student).filter(Student.id == student_id, Student.school_id == current_user.school_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")
    if student.is_transferred_externally:
        raise HTTPException(status_code=403, detail="Carteirinha indisponível — aluno transferido externamente")
    if not student.encrypted_qr_payload:
        student.encrypted_qr_payload = generate_encrypted_qr_payload(student, minimal_payload=True)
        db.commit()
    # Carteirinhas impressas precisam de alta tolerância a falhas (leitura noturna/portaria).
    import qrcode
    qr_b64 = generate_qr_code_base64(
        student.encrypted_qr_payload,
        size=16,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
    )
    class_ = db.query(Class).filter(Class.id == student.class_id).first()
    school = db.query(School).filter(School.id == student.school_id).first()
    shift = db.query(Shift).filter(Shift.id == class_.shift_id).first() if class_ else None

    # Validade = fim do ano letivo da turma, se houver; senão próximo ano.
    validity_year = class_.year if (class_ and class_.year) else (datetime.now().year + 1)
    validity = f"31/12/{validity_year}"

    return {
        "student_id": student.id,
        "full_name": student.full_name,
        "school_id": student.school_id,
        "school_name": school.name if school else None,
        "school_photo_url": school.photo_url if school else None,
        "class_id": student.class_id,
        "class_name": f"{class_.name} ({class_.grade})" if class_ else None,
        "shift_name": shift.name if shift else None,
        "qr_base64": qr_b64,
        "registration_code": student.registration_code,
        "photo_url": student.photo_url,
        "validity": validity,
    }


@router.post("/{student_id}/temporary-card", response_model=TemporaryCardResponse)
def create_temporary_card(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("super_admin", "school_admin", "secretary", "staff", module="students")),
):
    student = (
        db.query(Student)
        .filter(Student.id == student_id, Student.school_id == current_user.school_id, Student.is_active == True)
        .first()
    )
    if not student:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")
    if student.is_transferred_externally:
        raise HTTPException(status_code=403, detail="Carteirinha indisponível — aluno transferido externamente")

    class_ = db.query(Class).filter(Class.id == student.class_id).first()
    if not class_:
        raise HTTPException(status_code=400, detail="Aluno sem turma cadastrada")

    shift = db.query(Shift).filter(Shift.id == class_.shift_id, Shift.school_id == current_user.school_id).first()
    if not shift:
        raise HTTPException(status_code=400, detail="Turma do aluno não possui turno associado")

    today = date.today()
    today_iso = today.isoformat()

    end_time_str = shift.end_time or "17:00"
    try:
        hour, minute = map(int, end_time_str.split(":"))
    except Exception:
        hour, minute = 17, 0
    expires_at = datetime.combine(today, time(hour=hour, minute=minute))

    payload_dict = {
        "sid": student.id,
        "tmp": True,
        "d": today_iso,
        "s": shift.id,
        "e": expires_at.isoformat(),
    }
    encrypted_payload = generate_encrypted_qr_payload(payload_dict=payload_dict)
    qr_b64 = generate_qr_code_base64(encrypted_payload)

    temporary_card = TemporaryCard(
        student_id=student.id,
        shift_id=shift.id,
        date=today_iso,
        generated_by_user_id=current_user.id,
        expires_at=expires_at,
        qr_payload=encrypted_payload,
    )
    db.add(temporary_card)
    db.commit()
    db.refresh(temporary_card)

    school = db.query(School).filter(School.id == student.school_id).first()
    generated_by = db.query(User).filter(User.id == current_user.id).first()

    return {
        "id": temporary_card.id,
        "student_id": student.id,
        "student_name": student.full_name,
        "shift_id": shift.id,
        "shift_name": shift.name,
        "date": today_iso,
        "generated_at": temporary_card.generated_at,
        "generated_by_user_id": current_user.id,
        "generated_by_name": generated_by.full_name if generated_by else None,
        "expires_at": expires_at,
        "expires_at_iso": expires_at.isoformat(),
        "qr_payload": encrypted_payload,
        "qr_base64": qr_b64,
        "class_name": f"{class_.name} ({class_.grade})" if class_ else None,
        "school_name": school.name if school else None,
        "school_photo_url": school.photo_url if school else None,
        "registration_code": student.registration_code,
        "photo_url": student.photo_url,
        "validity_label": f"Válido até {end_time_str} de {today.strftime('%d/%m/%Y')}",
    }
