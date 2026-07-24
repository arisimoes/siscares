from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.core.security import get_current_user, require_role
from app.models import User, Module, SchoolModuleSetting
from app.schemas import ModuleResponse, SchoolModuleSettingResponse

router = APIRouter(prefix="/modules", tags=["modules"])


@router.get("", response_model=List[ModuleResponse])
def list_modules(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("super_admin")),
):
    return db.query(Module).all()


@router.get("/school/{school_id}", response_model=List[SchoolModuleSettingResponse])
def list_school_modules(
    school_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("super_admin")),
):
    return db.query(SchoolModuleSetting).filter(SchoolModuleSetting.school_id == school_id).all()


@router.post("/school/{school_id}/{module_id}")
def toggle_module(
    school_id: int,
    module_id: int,
    is_enabled: bool,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("super_admin")),
):
    setting = db.query(SchoolModuleSetting).filter(
        SchoolModuleSetting.school_id == school_id,
        SchoolModuleSetting.module_id == module_id,
    ).first()
    if not setting:
        setting = SchoolModuleSetting(school_id=school_id, module_id=module_id, is_enabled=is_enabled)
        db.add(setting)
    else:
        setting.is_enabled = is_enabled
    db.commit()
    db.refresh(setting)
    return setting
