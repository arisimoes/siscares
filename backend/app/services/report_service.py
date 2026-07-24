from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List
from datetime import datetime
from app.models import Attendance, Student, Class, Shift
from app.schemas import FrequencyReportItem, FrequencyReportResponse


def get_frequency_report(db: Session, school_id: int, month: str) -> FrequencyReportResponse:
    # month esperado no formato YYYY-MM
    items: List[FrequencyReportItem] = []

    classes = db.query(Class).filter(Class.school_id == school_id, Class.is_active == True).all()

    for cls in classes:
        students = db.query(Student).filter(Student.class_id == cls.id, Student.is_active == True).all()
        for student in students:
            total = db.query(Attendance).filter(
                Attendance.student_id == student.id,
                Attendance.date.like(f"{month}-%")
            ).count()
            present = db.query(Attendance).filter(
                Attendance.student_id == student.id,
                Attendance.date.like(f"{month}-%"),
                Attendance.status == "present"
            ).count()
            absent = db.query(Attendance).filter(
                Attendance.student_id == student.id,
                Attendance.date.like(f"{month}-%"),
                Attendance.status == "absent"
            ).count()
            justified = db.query(Attendance).filter(
                Attendance.student_id == student.id,
                Attendance.date.like(f"{month}-%"),
                Attendance.status == "justified"
            ).count()

            percentage = (present / total * 100) if total else 0.0
            items.append(FrequencyReportItem(
                class_id=cls.id,
                class_name=cls.name,
                student_id=student.id,
                student_name=student.full_name,
                total_classes=total,
                present_count=present,
                absent_count=absent,
                justified_count=justified,
                frequency_percentage=round(percentage, 2),
            ))

    return FrequencyReportResponse(school_id=school_id, month=month, items=items)
