import threading
import time
from datetime import datetime, date

from app.db.base import SessionLocal
from app.models import Shift, Class, Student, Attendance


_process_lock = threading.Lock()


def _minutes_from_time(t: str) -> int:
    if not t:
        return -1
    h, m = map(int, t.split(":"))
    return h * 60 + m


def close_shift_attendance(db, shift: Shift, today_iso: str):
    classes = db.query(Class).filter(
        Class.shift_id == shift.id,
        Class.is_active == True,
    ).all()
    class_ids = [c.id for c in classes]
    if not class_ids:
        return 0

    students = db.query(Student).filter(
        Student.class_id.in_(class_ids),
        Student.is_active == True,
        Student.school_id == shift.school_id,
    ).all()
    if not students:
        return 0

    created = 0
    for student in students:
        existing = db.query(Attendance).filter(
            Attendance.student_id == student.id,
            Attendance.shift_id == shift.id,
            Attendance.date == today_iso,
        ).first()
        if not existing:
            db.add(Attendance(
                student_id=student.id,
                shift_id=shift.id,
                date=today_iso,
                status="absent",
                registered_by_user_id=None,
            ))
            created += 1

    db.commit()
    return created


def _run_once():
    now = datetime.now()
    today_iso = date.today().isoformat()
    current_minutes = now.hour * 60 + now.minute

    db = SessionLocal()
    try:
        shifts = db.query(Shift).filter(Shift.is_active == True).all()
        for shift in shifts:
            end_minutes = _minutes_from_time(shift.end_time)
            if end_minutes < 0:
                continue
            # Fechamento 1 minuto após o término do turno
            if current_minutes > end_minutes:
                close_shift_attendance(db, shift, today_iso)
    finally:
        db.close()


def _scheduler_loop():
    while True:
        _run_once()
        time.sleep(60)


def start_attendance_scheduler():
    thread = threading.Thread(target=_scheduler_loop, daemon=True)
    thread.start()
