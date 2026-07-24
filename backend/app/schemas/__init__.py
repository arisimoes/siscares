from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional, List
from datetime import datetime


class SchoolBase(BaseModel):
    name: str
    cnpj: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None


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


class SchoolResponse(SchoolBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime


class UserPermissionBase(BaseModel):
    manage_classes: bool = False
    manage_students: bool = False
    manage_cards: bool = False
    manage_attendance: bool = False
    manage_reports: bool = False
    manage_transfers: bool = False
    manage_users: bool = False


class UserPermissionCreate(BaseModel):
    manage_classes: bool = False
    manage_students: bool = False
    manage_cards: bool = False
    manage_attendance: bool = False
    manage_reports: bool = False
    manage_transfers: bool = False
    manage_users: bool = False


class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: str


class UserCreate(UserBase):
    password: str
    school_id: Optional[int] = None
    permissions: Optional[UserPermissionCreate] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
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


class ClassCreate(ClassBase):
    pass


class ClassUpdate(BaseModel):
    name: Optional[str] = None
    grade: Optional[str] = None
    year: Optional[int] = None
    is_active: Optional[bool] = None


class ClassResponse(ClassBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    school_id: int
    is_active: bool
    created_at: datetime


class StudentBase(BaseModel):
    full_name: str
    birth_date: Optional[str] = None
    cpf: Optional[str] = None
    registration_code: Optional[str] = None
    class_id: Optional[int] = None


class StudentCreate(StudentBase):
    pass


class StudentUpdate(BaseModel):
    full_name: Optional[str] = None
    birth_date: Optional[str] = None
    cpf: Optional[str] = None
    registration_code: Optional[str] = None
    class_id: Optional[int] = None
    photo_url: Optional[str] = None
    is_active: Optional[bool] = None


class StudentResponse(StudentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    school_id: int
    encrypted_qr_payload: Optional[str] = None
    photo_url: Optional[str] = None
    is_active: bool
    created_at: datetime
    class_name: Optional[str] = None
    school_name: Optional[str] = None


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


class Token(BaseModel):
    access_token: str
    token_type: str


class LoginRequest(BaseModel):
    username: EmailStr
    password: str


class FrequencyReportItem(BaseModel):
    class_id: int
    class_name: str
    student_id: int
    student_name: str
    total_classes: int
    present_count: int
    absent_count: int
    justified_count: int
    frequency_percentage: float


class FrequencyReportResponse(BaseModel):
    school_id: int
    month: str  # YYYY-MM
    items: List[FrequencyReportItem]
