from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List
from datetime import datetime
from calendar import monthrange
from app.models import Attendance, Student, Class, Shift, SchoolCalendarDay
from app.schemas import FrequencyReportItem, FrequencyReportResponse


def _count_school_days(db: Session, school_id: int, year: int, month: int) -> int:
    _, last_day = monthrange(year, month)
    start = f"{year}-{month:02d}-01"
    end = f"{year}-{month:02d}-{last_day}"
    return db.query(SchoolCalendarDay).filter(
        SchoolCalendarDay.school_id == school_id,
        SchoolCalendarDay.date >= start,
        SchoolCalendarDay.date <= end,
        SchoolCalendarDay.day_type == "school",
    ).count()


def get_frequency_report(
    db: Session,
    school_id: int,
    month: str,
    class_id: int | None = None,
    day: str | None = None,
    student_name: str | None = None,
) -> FrequencyReportResponse:
    # month esperado no formato YYYY-MM
    items: List[FrequencyReportItem] = []

    query = db.query(Class).filter(Class.school_id == school_id, Class.is_active == True)
    if class_id:
        query = query.filter(Class.id == class_id)
    classes = query.order_by(Class.name.asc()).all()

    date_prefix = f"{day}" if day else f"{month}-%"

    # Conta dias letivos do mês via calendário escolar
    school_days_in_month = 0
    if not day:
        try:
            year, mon = map(int, month.split("-"))
            school_days_in_month = _count_school_days(db, school_id, year, mon)
        except ValueError:
            school_days_in_month = 0

    for cls in classes:
        student_query = db.query(Student).filter(
            Student.class_id == cls.id,
            Student.is_active == True,
            Student.school_id == school_id,
        )
        if student_name:
            student_query = student_query.filter(Student.full_name.ilike(f"%{student_name}%"))
        students = student_query.all()

        students = sorted(students, key=lambda s: s.full_name.lower())

        for student in students:
            filters = [
                Attendance.student_id == student.id,
                Attendance.date.like(date_prefix),
            ]
            present = db.query(Attendance).filter(*filters, Attendance.status == "present").count()
            absent = db.query(Attendance).filter(*filters, Attendance.status == "absent").count()
            justified = db.query(Attendance).filter(*filters, Attendance.status == "justified").count()

            # Base: dias letivos do calendário; justificadas não reduzem frequência
            effective_base = school_days_in_month if (school_days_in_month and not day) else (present + absent)
            attended = present + justified
            percentage = (attended / effective_base * 100) if effective_base else 0.0

            items.append(FrequencyReportItem(
                class_id=cls.id,
                class_name=cls.name,
                student_id=student.id,
                student_name=student.full_name,
                total_classes=effective_base,
                present_count=present,
                absent_count=absent,
                justified_count=justified,
                frequency_percentage=round(percentage, 2),
            ))

    return FrequencyReportResponse(school_id=school_id, month=month, items=items)
