from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.core.security import get_current_user, require_role
from app.models import User, School, Class, Shift, Student
from app.schemas import ClassCreate, ClassResponse, ClassUpdate, ShiftCreate, ShiftResponse
from app.core.module_guard import require_module_for_current_school

router = APIRouter(prefix="/classes", tags=["classes"])


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
    return db.query(Class).filter(Class.school_id == current_user.school_id, Class.is_active == True).all()


@router.post("", response_model=ClassResponse, status_code=status.HTTP_201_CREATED)
def create_class(
    payload: ClassCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("school_admin", "secretary", "staff", module="classes")),
):
    cls = Class(school_id=current_user.school_id, **payload.model_dump())
    db.add(cls)
    db.commit()
    db.refresh(cls)
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
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(cls, field, value)
    db.commit()
    db.refresh(cls)
    return cls
