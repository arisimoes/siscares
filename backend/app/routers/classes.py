from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.core.security import get_current_user, require_role
from app.models import User, School, Class, Shift, Student, SchoolAcademicYear
from app.schemas import ClassCreate, ClassResponse, ClassUpdate, ShiftCreate, ShiftResponse
from app.core.module_guard import require_module_for_current_school
from app.services.attendance_scheduler import close_shift_attendance


def _require_academic_year(db: Session, school_id: int, year: int):
    if not year:
        return
    exists = db.query(SchoolAcademicYear).filter(
        SchoolAcademicYear.school_id == school_id,
        SchoolAcademicYear.year == year,
    ).first()
    if not exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ano letivo {year} não cadastrado. Cadastre-o no calendário escolar primeiro.",
        )

router = APIRouter(prefix="/classes", tags=["classes"])


def _shift_name(db, shift_id: int | None) -> str | None:
    if not shift_id:
        return None
    shift = db.query(Shift).filter(Shift.id == shift_id).first()
    return shift.name if shift else None


@router.get("/shifts", response_model=List[ShiftResponse])
def list_shifts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Shift).filter(Shift.school_id == current_user.school_id, Shift.is_active == True).all()


@router.post("/shifts", response_model=ShiftResponse, status_code=status.HTTP_201_CREATED)
def create_shift(
    payload: ShiftCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("school_admin", "secretary", "staff", module="classes")),
):
    shift = Shift(school_id=current_user.school_id, **payload.model_dump())
    db.add(shift)
    db.commit()
    db.refresh(shift)
    return shift


@router.get("", response_model=List[ClassResponse])
def list_classes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    classes = db.query(Class).filter(Class.school_id == current_user.school_id, Class.is_active == True).all()
    for cls in classes:
        cls.shift_name = _shift_name(db, cls.shift_id)
    return classes


@router.post("", response_model=ClassResponse, status_code=status.HTTP_201_CREATED)
def create_class(
    payload: ClassCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("school_admin", "secretary", "staff", module="classes")),
):
    _require_academic_year(db, current_user.school_id, payload.year)
    cls = Class(school_id=current_user.school_id, **payload.model_dump())
    db.add(cls)
    db.commit()
    db.refresh(cls)
    cls.shift_name = _shift_name(db, cls.shift_id)
    return cls


@router.put("/{class_id}", response_model=ClassResponse)
def update_class(
    class_id: int,
    payload: ClassUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("school_admin", "secretary", "staff", module="classes")),
):
    cls = db.query(Class).filter(Class.id == class_id, Class.school_id == current_user.school_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="Turma não encontrada")
    data = payload.model_dump(exclude_unset=True)
    if "year" in data:
        _require_academic_year(db, current_user.school_id, data["year"])
    for field, value in data.items():
        setattr(cls, field, value)
    db.commit()
    db.refresh(cls)
    cls.shift_name = _shift_name(db, cls.shift_id)
    return cls


@router.delete("/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_class(
    class_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("school_admin", "secretary", "staff", module="classes")),
):
    cls = db.query(Class).filter(Class.id == class_id, Class.school_id == current_user.school_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="Turma não encontrada")
    cls.is_active = False
    db.commit()
    return None


@router.post("/close-shift/{shift_id}")
def close_shift(
    shift_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("school_admin", "secretary", "staff", module="attendance")),
):
    from datetime import date
    shift = db.query(Shift).filter(Shift.id == shift_id, Shift.school_id == current_user.school_id).first()
    if not shift:
        raise HTTPException(status_code=404, detail="Turno não encontrado")
    created = close_shift_attendance(db, shift, date.today().isoformat())
    return {"created": created}
