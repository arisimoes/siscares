from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.db.session import get_db
from app.core.security import get_current_user, require_role
from app.models import User, School, SchoolAcademicYear, SchoolCalendarDay
from app.schemas import (
    AcademicYearCreate,
    AcademicYearUpdate,
    AcademicYearResponse,
    CalendarDayCreate,
    CalendarDayUpdate,
    CalendarDayResponse,
)

router = APIRouter(prefix="/calendar", tags=["calendar"])


def _require_school_access(current_user: User, school_id: int):
    if current_user.role == "super_admin":
        return
    if current_user.role in {"school_admin", "secretary", "staff"} and current_user.school_id == school_id:
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissão insuficiente")


@router.get("/school/{school_id}/years", response_model=List[AcademicYearResponse])
def list_academic_years(
    school_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("super_admin", "school_admin", "secretary", "staff", module="calendar")),
):
    _require_school_access(current_user, school_id)
    return db.query(SchoolAcademicYear).filter(SchoolAcademicYear.school_id == school_id).order_by(SchoolAcademicYear.year.desc()).all()


@router.post("/school/{school_id}/years", response_model=AcademicYearResponse, status_code=status.HTTP_201_CREATED)
def create_academic_year(
    school_id: int,
    payload: AcademicYearCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("super_admin", "school_admin", "secretary", "staff", module="calendar")),
):
    _require_school_access(current_user, school_id)
    existing = db.query(SchoolAcademicYear).filter(
        SchoolAcademicYear.school_id == school_id,
        SchoolAcademicYear.year == payload.year,
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ano letivo já existe")
    year = SchoolAcademicYear(
        school_id=school_id,
        year=payload.year,
        start_date=payload.start_date,
        end_date=payload.end_date,
    )
    db.add(year)
    db.commit()
    db.refresh(year)
    return year


@router.put("/school/{school_id}/years/{year_id}", response_model=AcademicYearResponse)
def update_academic_year(
    school_id: int,
    year_id: int,
    payload: AcademicYearUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("super_admin", "school_admin", "secretary", "staff", module="calendar")),
):
    _require_school_access(current_user, school_id)
    year = db.query(SchoolAcademicYear).filter(
        SchoolAcademicYear.id == year_id,
        SchoolAcademicYear.school_id == school_id,
    ).first()
    if not year:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ano letivo não encontrado")
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(year, field, value)
    db.commit()
    db.refresh(year)
    return year


@router.get("/school/{school_id}/days", response_model=List[CalendarDayResponse])
def list_calendar_days(
    school_id: int,
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("super_admin", "school_admin", "secretary", "staff", module="calendar")),
):
    _require_school_access(current_user, school_id)
    query = db.query(SchoolCalendarDay).filter(SchoolCalendarDay.school_id == school_id)
    if year:
        academic_year = db.query(SchoolAcademicYear).filter(
            SchoolAcademicYear.school_id == school_id,
            SchoolAcademicYear.year == year,
        ).first()
        if academic_year:
            query = query.filter(
                SchoolCalendarDay.date >= academic_year.start_date,
                SchoolCalendarDay.date <= academic_year.end_date,
            )
        else:
            start = f"{year}-01-01"
            end = f"{year}-12-31"
            query = query.filter(SchoolCalendarDay.date >= start, SchoolCalendarDay.date <= end)
    return query.order_by(SchoolCalendarDay.date).all()


@router.post("/school/{school_id}/days", response_model=CalendarDayResponse, status_code=status.HTTP_201_CREATED)
def create_or_update_calendar_day(
    school_id: int,
    payload: CalendarDayCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("super_admin", "school_admin", "secretary", "staff", module="calendar")),
):
    _require_school_access(current_user, school_id)
    day = db.query(SchoolCalendarDay).filter(
        SchoolCalendarDay.school_id == school_id,
        SchoolCalendarDay.date == payload.date,
    ).first()
    if day:
        day.day_type = payload.day_type
        day.description = payload.description
    else:
        day = SchoolCalendarDay(
            school_id=school_id,
            date=payload.date,
            day_type=payload.day_type,
            description=payload.description,
        )
        db.add(day)
    db.commit()
    db.refresh(day)
    return day


@router.put("/school/{school_id}/days/{day_id}", response_model=CalendarDayResponse)
def update_calendar_day(
    school_id: int,
    day_id: int,
    payload: CalendarDayUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("super_admin", "school_admin", "secretary", "staff", module="calendar")),
):
    _require_school_access(current_user, school_id)
    day = db.query(SchoolCalendarDay).filter(
        SchoolCalendarDay.id == day_id,
        SchoolCalendarDay.school_id == school_id,
    ).first()
    if not day:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dia não encontrado")
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(day, field, value)
    db.commit()
    db.refresh(day)
    return day


@router.delete("/school/{school_id}/days/{day_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_calendar_day(
    school_id: int,
    day_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("super_admin", "school_admin", "secretary", "staff", module="calendar")),
):
    _require_school_access(current_user, school_id)
    day = db.query(SchoolCalendarDay).filter(
        SchoolCalendarDay.id == day_id,
        SchoolCalendarDay.school_id == school_id,
    ).first()
    if not day:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dia não encontrado")
    db.delete(day)
    db.commit()
    return None


@router.post("/school/{school_id}/generate/{year}")
def generate_default_calendar(
    school_id: int,
    year: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("super_admin", "school_admin", "secretary", "staff", module="calendar")),
):
    _require_school_access(current_user, school_id)
    academic_year = db.query(SchoolAcademicYear).filter(
        SchoolAcademicYear.school_id == school_id,
        SchoolAcademicYear.year == year,
    ).first()
    if not academic_year:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ano letivo não encontrado. Cadastre-o primeiro.")

    start = datetime.strptime(academic_year.start_date, "%Y-%m-%d").date()
    end = datetime.strptime(academic_year.end_date, "%Y-%m-%d").date()

    current = start
    created = 0
    updated = 0
    while current <= end:
        date_str = current.strftime("%Y-%m-%d")
        day_type = "weekend" if current.weekday() >= 5 else "school"
        existing = db.query(SchoolCalendarDay).filter(
            SchoolCalendarDay.school_id == school_id,
            SchoolCalendarDay.date == date_str,
        ).first()
        if existing:
            if existing.day_type == "school" and day_type == "weekend":
                existing.day_type = "weekend"
                updated += 1
        else:
            db.add(SchoolCalendarDay(
                school_id=school_id,
                date=date_str,
                day_type=day_type,
            ))
            created += 1
        current += timedelta(days=1)
    db.commit()
    return {"created": created, "updated": updated}
