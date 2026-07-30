from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime


class SchoolBase(BaseModel):
    name: str
    cnpj: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    photo_url: Optional[str] = None


class SchoolCreate(SchoolBase):
    pass


class SchoolUpdate(BaseModel):
    name: Optional[str] = None
    cnpj: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    is_active: Optional[bool] = None
    photo_url: Optional[str] = None


class SchoolResponse(SchoolBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime
    photo_url: Optional[str] = None


class UserPermissionBase(BaseModel):
    manage_classes: bool = False
    manage_students: bool = False
    manage_cards: bool = False
    manage_attendance: bool = False
    manage_reports: bool = False
    manage_transfers: bool = False
    manage_users: bool = False
    manage_calendar: bool = False
    manage_logs: bool = False


class UserPermissionCreate(BaseModel):
    manage_classes: bool = False
    manage_students: bool = False
    manage_cards: bool = False
    manage_attendance: bool = False
    manage_reports: bool = False
    manage_transfers: bool = False
    manage_users: bool = False
    manage_calendar: bool = False
    manage_logs: bool = False


class UserBase(BaseModel):
    email: str
    full_name: str
    role: str


class UserCreate(UserBase):
    password: str
    school_id: Optional[int] = None
    permissions: Optional[UserPermissionCreate] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    school_id: Optional[int] = None
    permissions: Optional[UserPermissionCreate] = None


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    school_id: Optional[int]
    is_active: bool
    created_at: datetime
    permissions: Optional[UserPermissionBase] = None


class ShiftBase(BaseModel):
    name: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None


class ShiftCreate(ShiftBase):
    pass


class ShiftResponse(ShiftBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    school_id: int
    is_active: bool


class ClassBase(BaseModel):
    name: str
    grade: Optional[str] = None
    year: int


class ClassCreate(BaseModel):
    name: str
    grade: Optional[str] = None
    year: int
    shift_id: Optional[int] = None


class ClassUpdate(BaseModel):
    name: Optional[str] = None
    grade: Optional[str] = None
    year: Optional[int] = None
    shift_id: Optional[int] = None
    is_active: Optional[bool] = None


class ClassResponse(ClassBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    school_id: int
    shift_id: Optional[int] = None
    shift_name: Optional[str] = None
    is_active: bool
    created_at: datetime


class StudentBase(BaseModel):
    full_name: str
    birth_date: Optional[str] = None
    cpf: Optional[str] = None
    registration_code: Optional[str] = None
    class_id: Optional[int] = None
    bolsa_familia: bool = False


class StudentCreate(StudentBase):
    pass


class StudentUpdate(BaseModel):
    full_name: Optional[str] = None
    birth_date: Optional[str] = None
    cpf: Optional[str] = None
    registration_code: Optional[str] = None
    class_id: Optional[int] = None
    photo_url: Optional[str] = None
    bolsa_familia: Optional[bool] = None
    is_active: Optional[bool] = None


class StudentResponse(StudentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    school_id: int
    encrypted_qr_payload: Optional[str] = None
    photo_url: Optional[str] = None
    is_active: bool
    is_transferred_externally: bool = False
    created_at: datetime
    class_name: Optional[str] = None
    shift_name: Optional[str] = None
    school_name: Optional[str] = None
    school_photo_url: Optional[str] = None


class StudentDeleteRequest(BaseModel):
    password: str


class AttendanceBase(BaseModel):
    student_id: int
    shift_id: int
    date: str
    status: str = "present"


class AttendanceCreate(BaseModel):
    qr_payload: str
    shift_id: int


class AttendanceResponse(AttendanceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    registered_at: datetime
    registered_by_user_id: Optional[int]
    justification: Optional[str] = None


class JustifyAbsenceRequest(BaseModel):
    date: str
    justification: str


class TransferHistoryBase(BaseModel):
    student_id: int
    from_class_id: Optional[int] = None
    to_class_id: Optional[int] = None
    transfer_type: str = "internal"
    reason: Optional[str] = None


class TransferHistoryCreate(TransferHistoryBase):
    pass


class TransferHistoryResponse(TransferHistoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    transferred_at: datetime
    registered_by_user_id: Optional[int] = None
    student_name: Optional[str] = None
    from_class_name: Optional[str] = None
    to_class_name: Optional[str] = None
    registered_by_name: Optional[str] = None


class LogEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    student_id: int
    student_name: str
    date: Optional[str] = None
    from_class_name: Optional[str] = None
    to_class_name: Optional[str] = None
    reason: Optional[str] = None
    registered_by_name: Optional[str] = None
    registered_at: datetime


class ModuleBase(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    is_core: bool = False


class ModuleResponse(ModuleBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class SchoolModuleSettingBase(BaseModel):
    school_id: int
    module_id: int
    is_enabled: bool = False


class SchoolModuleSettingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    school_id: int
    module: ModuleResponse
    is_enabled: bool


class AcademicYearBase(BaseModel):
    year: int
    start_date: str
    end_date: str


class AcademicYearCreate(AcademicYearBase):
    pass


class AcademicYearUpdate(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_active: Optional[bool] = None


class AcademicYearResponse(AcademicYearBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    school_id: int
    is_active: bool


class CalendarDayBase(BaseModel):
    date: str
    day_type: str = "school"  # school, holiday, event, weekend
    description: Optional[str] = None


class CalendarDayCreate(CalendarDayBase):
    pass


class CalendarDayUpdate(BaseModel):
    day_type: Optional[str] = None
    description: Optional[str] = None


class CalendarDayResponse(CalendarDayBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    school_id: int


class Token(BaseModel):
    access_token: str
    token_type: str


class LoginRequest(BaseModel):
    login: str
    password: str


class FrequencyReportItem(BaseModel):
    class_id: int
    class_name: str
    class_year: int
    student_id: int
    student_name: str
    bolsa_familia: bool = False
    total_classes: int
    present_count: int
    absent_count: int
    justified_count: int
    frequency_percentage: float


class FrequencyReportResponse(BaseModel):
    school_id: int
    month: str  # YYYY-MM
    items: List[FrequencyReportItem]
