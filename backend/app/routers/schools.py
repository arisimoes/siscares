from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pathlib import Path

from app.db.session import get_db
from app.core.security import get_current_user, require_role
from app.core.config import settings
from app.models import (
    User, School, UserPermission, Student, Class, Shift, Attendance,
    TransferHistory, SchoolModuleSetting, SchoolCalendarDay, SchoolAcademicYear
)
from app.schemas import SchoolCreate, SchoolResponse, SchoolUpdate

router = APIRouter(prefix="/schools", tags=["schools"])


@router.get("", response_model=List[SchoolResponse])
def list_schools(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("super_admin")),
):
    return db.query(School).all()


@router.post("", response_model=SchoolResponse, status_code=status.HTTP_201_CREATED)
def create_school(
    payload: SchoolCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("super_admin")),
):
    school = School(**payload.model_dump())
    db.add(school)
    db.commit()
    db.refresh(school)
    return school


@router.get("/{school_id}", response_model=SchoolResponse)
def get_school(
    school_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("super_admin")),
):
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="Escola não encontrada")
    return school


@router.put("/{school_id}", response_model=SchoolResponse)
def update_school(
    school_id: int,
    payload: SchoolUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("super_admin")),
):
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="Escola não encontrada")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(school, field, value)
    db.commit()
    db.refresh(school)
    return school


@router.delete("/{school_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_school(
    school_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("super_admin")),
):
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="Escola não encontrada")

    # Remove foto do disco, se existir
    if school.photo_url:
        photo_path = Path(settings.UPLOAD_DIR) / school.photo_url.replace("/static/uploads/", "")
        try:
            if photo_path.exists():
                photo_path.unlink()
        except Exception:
            pass

    # Exclui todos os dados relacionados à escola em cascata
    db.query(Attendance).filter(Attendance.student_id.in_(
        db.query(Student.id).filter(Student.school_id == school_id)
    )).delete(synchronize_session=False)

    db.query(TransferHistory).filter(TransferHistory.student_id.in_(
        db.query(Student.id).filter(Student.school_id == school_id)
    )).delete(synchronize_session=False)

    db.query(UserPermission).filter(UserPermission.user_id.in_(
        db.query(User.id).filter(User.school_id == school_id)
    )).delete(synchronize_session=False)

    db.query(User).filter(User.school_id == school_id).delete(synchronize_session=False)
    db.query(Student).filter(Student.school_id == school_id).delete(synchronize_session=False)
    db.query(Class).filter(Class.school_id == school_id).delete(synchronize_session=False)
    db.query(Shift).filter(Shift.school_id == school_id).delete(synchronize_session=False)
    db.query(SchoolModuleSetting).filter(SchoolModuleSetting.school_id == school_id).delete(synchronize_session=False)
    db.query(SchoolCalendarDay).filter(SchoolCalendarDay.school_id == school_id).delete(synchronize_session=False)
    db.query(SchoolAcademicYear).filter(SchoolAcademicYear.school_id == school_id).delete(synchronize_session=False)

    db.delete(school)
    db.commit()
    return None
