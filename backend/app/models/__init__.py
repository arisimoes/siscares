from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base


class School(Base):
    __tablename__ = "schools"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    cnpj = Column(String(20), unique=True, nullable=True)
    phone = Column(String(30), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(2), nullable=True)
    photo_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    users = relationship("User", back_populates="school", lazy="selectin")
    students = relationship("Student", back_populates="school", lazy="selectin")
    classes = relationship("Class", back_populates="school", lazy="selectin")
    shifts = relationship("Shift", back_populates="school", lazy="selectin")
    module_settings = relationship("SchoolModuleSetting", back_populates="school", lazy="selectin")
    calendar_days = relationship("SchoolCalendarDay", back_populates="school", lazy="selectin", cascade="all, delete-orphan")
    academic_years = relationship("SchoolAcademicYear", back_populates="school", lazy="selectin", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="school_admin")  # super_admin, school_admin, staff
    is_active = Column(Boolean, default=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    school = relationship("School", back_populates="users")
    permissions = relationship("UserPermission", back_populates="user", uselist=False, lazy="selectin", cascade="all, delete-orphan")


class UserPermission(Base):
    __tablename__ = "user_permissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    manage_classes = Column(Boolean, default=False)
    manage_students = Column(Boolean, default=False)
    manage_cards = Column(Boolean, default=False)
    manage_attendance = Column(Boolean, default=False)
    manage_reports = Column(Boolean, default=False)
    manage_transfers = Column(Boolean, default=False)
    manage_users = Column(Boolean, default=False)
    manage_calendar = Column(Boolean, default=False)
    manage_logs = Column(Boolean, default=False)

    user = relationship("User", back_populates="permissions", passive_deletes=True)


class Shift(Base):
    __tablename__ = "shifts"

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    name = Column(String(100), nullable=False)  # matutino, vespertino, noturno
    start_time = Column(String(5), nullable=True)  # HH:MM
    end_time = Column(String(5), nullable=True)
    is_active = Column(Boolean, default=True)

    school = relationship("School", back_populates="shifts")
    attendances = relationship("Attendance", back_populates="shift")


class Class(Base):
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    shift_id = Column(Integer, ForeignKey("shifts.id"), nullable=True)
    name = Column(String(100), nullable=False)
    grade = Column(String(50), nullable=True)  # 1º ano, 2º ano etc.
    year = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    school = relationship("School", back_populates="classes")
    shift = relationship("Shift")
    students = relationship("Student", back_populates="class_")


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=True)
    full_name = Column(String(255), nullable=False)
    birth_date = Column(String(10), nullable=True)
    cpf = Column(String(14), nullable=True)
    registration_code = Column(String(50), nullable=True)
    photo_url = Column(String(500), nullable=True)
    encrypted_qr_payload = Column(Text, nullable=True)
    bolsa_familia = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    school = relationship("School", back_populates="students")
    class_ = relationship("Class", back_populates="students")
    attendances = relationship("Attendance", back_populates="student")
    transfers = relationship("TransferHistory", back_populates="student")


class Attendance(Base):
    __tablename__ = "attendances"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    shift_id = Column(Integer, ForeignKey("shifts.id"), nullable=False)
    date = Column(String(10), nullable=False)  # YYYY-MM-DD
    status = Column(String(20), nullable=False, default="present")  # present, absent, justified
    justification = Column(Text, nullable=True)
    registered_at = Column(DateTime, default=datetime.utcnow)
    registered_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    student = relationship("Student", back_populates="attendances")
    shift = relationship("Shift", back_populates="attendances")

    __table_args__ = (
        UniqueConstraint("student_id", "shift_id", "date", name="uix_attendance_student_shift_date"),
    )


class TransferHistory(Base):
    __tablename__ = "transfer_history"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    from_class_id = Column(Integer, ForeignKey("classes.id"), nullable=True)
    to_class_id = Column(Integer, ForeignKey("classes.id"), nullable=True)
    transfer_type = Column(String(50), nullable=False, default="internal")  # internal, external
    reason = Column(Text, nullable=True)
    transferred_at = Column(DateTime, default=datetime.utcnow)
    registered_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    student = relationship("Student", back_populates="transfers")
    from_class = relationship("Class", foreign_keys=[from_class_id])
    to_class = relationship("Class", foreign_keys=[to_class_id])
    registered_by = relationship("User")


class Module(Base):
    __tablename__ = "modules"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_core = Column(Boolean, default=False)

    school_settings = relationship("SchoolModuleSetting", back_populates="module")


class SchoolModuleSetting(Base):
    __tablename__ = "school_module_settings"

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    module_id = Column(Integer, ForeignKey("modules.id"), nullable=False)
    is_enabled = Column(Boolean, default=False)

    school = relationship("School", back_populates="module_settings")
    module = relationship("Module", back_populates="school_settings")

    __table_args__ = (
        UniqueConstraint("school_id", "module_id", name="uix_school_module"),
    )


class SchoolAcademicYear(Base):
    __tablename__ = "school_academic_years"

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    year = Column(Integer, nullable=False)
    start_date = Column(String(10), nullable=False)  # YYYY-MM-DD
    end_date = Column(String(10), nullable=False)    # YYYY-MM-DD
    is_active = Column(Boolean, default=True)

    school = relationship("School", back_populates="academic_years")

    __table_args__ = (
        UniqueConstraint("school_id", "year", name="uix_school_academic_year"),
    )


class SchoolCalendarDay(Base):
    __tablename__ = "school_calendar_days"

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    date = Column(String(10), nullable=False)  # YYYY-MM-DD
    day_type = Column(String(20), nullable=False, default="school")  # school, holiday, event, weekend
    description = Column(Text, nullable=True)

    school = relationship("School", back_populates="calendar_days")

    __table_args__ = (
        UniqueConstraint("school_id", "date", name="uix_school_calendar_day"),
    )
