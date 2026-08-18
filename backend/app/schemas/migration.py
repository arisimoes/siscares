from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime


class MigrationSourceClass(BaseModel):
    id: int
    name: str
    grade: Optional[str] = None
    year: int
    shift_id: Optional[int] = None
    shift_name: Optional[str] = None
    student_count: int


class MigrationStudent(BaseModel):
    id: int
    full_name: str
    registration_code: Optional[str] = None
    birth_date: Optional[str] = None
    current_class_id: Optional[int] = None
    current_class_name: Optional[str] = None


class MigrationTargetClass(BaseModel):
    id: int
    name: str
    grade: Optional[str] = None
    year: int
    shift_id: Optional[int] = None
    shift_name: Optional[str] = None


class MigrationListResponse(BaseModel):
    source_year: int
    target_year: Optional[int] = None
    classes: List[MigrationSourceClass]
    students: List[MigrationStudent]


class MigrationRequest(BaseModel):
    student_ids: List[int]
    target_class_id: int


class MigrationResultItem(BaseModel):
    student_id: int
    full_name: str
    success: bool
    detail: Optional[str] = None
    new_class_name: Optional[str] = None


class MigrationResponse(BaseModel):
    migrated: int
    failed: int
    results: List[MigrationResultItem]
