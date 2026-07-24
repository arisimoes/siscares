from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.core.security import get_current_user, require_role
from app.models import User, School
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
