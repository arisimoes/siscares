from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import SchoolModuleSetting, Module


def is_module_enabled(db: Session, school_id: int, module_code: str) -> bool:
    if not school_id:
        return False
    module = db.query(Module).filter(Module.code == module_code).first()
    if not module:
        return False
    setting = db.query(SchoolModuleSetting).filter(
        SchoolModuleSetting.school_id == school_id,
        SchoolModuleSetting.module_id == module.id,
    ).first()
    if setting:
        return setting.is_enabled
    # Se não existir configuração, módulos core vêm habilitados por padrão
    return module.is_core


def require_module_for_current_school(db: Session, current_user, module_code: str):
    if not is_module_enabled(db, current_user.school_id, module_code):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Módulo '{module_code}' não está habilitado para esta escola",
        )
