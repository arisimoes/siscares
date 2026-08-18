from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime

from app.db.session import get_db
from app.core.security import get_current_user, require_role
from app.models import User, Student, Class, SchoolAcademicYear
from app.schemas.migration import (
    MigrationListResponse,
    MigrationSourceClass,
    MigrationStudent,
    MigrationTargetClass,
    MigrationRequest,
    MigrationResponse,
    MigrationResultItem,
)
from app.services.qr_service import generate_encrypted_qr_payload
from app.models import TransferHistory  # noqa: E402

router = APIRouter(prefix="/migration", tags=["migration"])


def _require_school_access(current_user: User, school_id: int):
    if current_user.role == "super_admin":
        return
    if current_user.role in {"school_admin", "secretary", "staff"} and current_user.school_id == school_id:
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissão insuficiente")


def _shift_name(db: Session, shift_id: Optional[int]) -> Optional[str]:
    from app.models import Shift
    if not shift_id:
        return None
    shift = db.query(Shift).filter(Shift.id == shift_id).first()
    return shift.name if shift else None


@router.get("/available-years")
def list_available_years(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("super_admin", "school_admin", "secretary", "staff", module="migration")),
):
    _require_school_access(current_user, current_user.school_id)
    years = db.query(SchoolAcademicYear.year).filter(
        SchoolAcademicYear.school_id == current_user.school_id,
        SchoolAcademicYear.is_active == True,
    ).distinct().order_by(SchoolAcademicYear.year.desc()).all()
    return [y[0] for y in years]


@router.get("/classes/{year}", response_model=List[MigrationTargetClass])
def list_classes_by_year(
    year: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("super_admin", "school_admin", "secretary", "staff", module="migration")),
):
    _require_school_access(current_user, current_user.school_id)
    classes = db.query(Class).filter(
        Class.school_id == current_user.school_id,
        Class.year == year,
        Class.is_active == True,
    ).order_by(Class.name).all()
    result = []
    for cls in classes:
        result.append(MigrationTargetClass(
            id=cls.id,
            name=cls.name,
            grade=cls.grade,
            year=cls.year,
            shift_id=cls.shift_id,
            shift_name=_shift_name(db, cls.shift_id),
        ))
    return result


@router.get("/students", response_model=MigrationListResponse)
def list_migration_students(
    source_year: int,
    class_id: Optional[int] = None,
    name: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("super_admin", "school_admin", "secretary", "staff", module="migration")),
):
    _require_school_access(current_user, current_user.school_id)

    # Determina o próximo ano letivo cadastrado após o source_year.
    next_year_row = db.query(SchoolAcademicYear).filter(
        SchoolAcademicYear.school_id == current_user.school_id,
        SchoolAcademicYear.year > source_year,
        SchoolAcademicYear.is_active == True,
    ).order_by(SchoolAcademicYear.year.asc()).first()

    # Turmas do ano de origem com contagem de alunos ativos.
    class_query = db.query(Class).filter(
        Class.school_id == current_user.school_id,
        Class.year == source_year,
        Class.is_active == True,
    )
    if class_id:
        class_query = class_query.filter(Class.id == class_id)
    classes = class_query.order_by(Class.name).all()

    class_ids = [cls.id for cls in classes]

    student_query = db.query(Student).filter(
        Student.school_id == current_user.school_id,
        Student.is_active == True,
        Student.is_transferred_externally == False,
        Student.class_id.in_(class_ids),
    )
    if name:
        student_query = student_query.filter(Student.full_name.ilike(f"%{name}%"))
    students = student_query.order_by(Student.full_name).all()

    student_count_by_class = dict(
        db.query(Student.class_id, func.count(Student.id)).filter(
            Student.school_id == current_user.school_id,
            Student.is_active == True,
            Student.is_transferred_externally == False,
            Student.class_id.in_(class_ids),
        ).group_by(Student.class_id).all()
    )

    source_classes = []
    for cls in classes:
        source_classes.append(MigrationSourceClass(
            id=cls.id,
            name=cls.name,
            grade=cls.grade,
            year=cls.year,
            shift_id=cls.shift_id,
            shift_name=_shift_name(db, cls.shift_id),
            student_count=student_count_by_class.get(cls.id, 0),
        ))

    student_list = []
    for s in students:
        cls = next((c for c in classes if c.id == s.class_id), None)
        student_list.append(MigrationStudent(
            id=s.id,
            full_name=s.full_name,
            registration_code=s.registration_code,
            birth_date=s.birth_date,
            current_class_id=s.class_id,
            current_class_name=f"{cls.name} ({cls.grade})" if cls else None,
        ))

    return MigrationListResponse(
        source_year=source_year,
        target_year=next_year_row.year if next_year_row else None,
        classes=source_classes,
        students=student_list,
    )


@router.post("/migrate", response_model=MigrationResponse)
def migrate_students(
    payload: MigrationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("super_admin", "school_admin", "secretary", "staff", module="migration")),
):
    _require_school_access(current_user, current_user.school_id)

    target_class = db.query(Class).filter(
        Class.id == payload.target_class_id,
        Class.school_id == current_user.school_id,
        Class.is_active == True,
    ).first()
    if not target_class:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Turma de destino não encontrada")

    target_year_row = db.query(SchoolAcademicYear).filter(
        SchoolAcademicYear.school_id == current_user.school_id,
        SchoolAcademicYear.year == target_class.year,
        SchoolAcademicYear.is_active == True,
    ).first()
    if not target_year_row:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ano letivo {target_class.year} não está cadastrado ou ativo. Cadastre-o no calendário escolar primeiro.",
        )

    results = []
    migrated = 0
    failed = 0

    for student_id in payload.student_ids:
        student = db.query(Student).filter(
            Student.id == student_id,
            Student.school_id == current_user.school_id,
            Student.is_active == True,
            Student.is_transferred_externally == False,
        ).first()
        if not student:
            results.append(MigrationResultItem(
                student_id=student_id,
                full_name="",
                success=False,
                detail="Aluno não encontrado, inativo ou transferido externamente",
            ))
            failed += 1
            continue

        old_class_id = student.class_id
        student.class_id = target_class.id
        student.encrypted_qr_payload = generate_encrypted_qr_payload(student, minimal_payload=True)
        db.flush()

        from app.models import TransferHistory
        transfer = TransferHistory(
            student_id=student.id,
            from_class_id=old_class_id,
            to_class_id=target_class.id,
            transfer_type="internal",
            reason=f"Migração automática para o ano letivo {target_class.year}",
            registered_by_user_id=current_user.id,
        )
        db.add(transfer)

        results.append(MigrationResultItem(
            student_id=student.id,
            full_name=student.full_name,
            success=True,
            new_class_name=f"{target_class.name} ({target_class.grade})" if target_class.grade else target_class.name,
        ))
        migrated += 1

    db.commit()
    return MigrationResponse(migrated=migrated, failed=failed, results=results)
