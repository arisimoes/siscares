from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        raise credentials_exception
    return user


SCHOOL_ROLES = {"school_admin", "secretary", "staff"}

# Mapeamento de permissões para verificação granular (apenas non-admins)
PERMISSION_MODULE_MAP = {
    "classes": "manage_classes",
    "students": "manage_students",
    "cards": "manage_cards",
    "attendance": "manage_attendance",
    "reports": "manage_reports",
    "transfers": "manage_transfers",
    "users": "manage_users",
    "calendar": "manage_calendar",
    "logs": "manage_logs",
    "migration": "manage_migration",
}


def require_role(*roles: str, module: str = None):
    """Decorator de permissão. Se algum papel escolar estiver em roles,
    aceita qualquer papel de gestão escolar (school_admin/secretary/staff).
    Se module for informado e usuário não for gestor, verifica permissão granular."""
    allowed = set(roles)
    allow_any_school_manager = bool(allowed & SCHOOL_ROLES)

    def checker(current_user: User = Depends(get_current_user)):
        if current_user.role == "super_admin":
            return current_user
        if current_user.role in allowed:
            return current_user
        if allow_any_school_manager and current_user.role in SCHOOL_ROLES:
            # Gestor escolar continua com acesso total a módulos escolares
            if current_user.role == "school_admin":
                return current_user
            # Staff/secretary: só passam se tiver permissão granular para o módulo
            if module:
                perm_key = PERMISSION_MODULE_MAP.get(module)
                if perm_key and current_user.permissions and getattr(current_user.permissions, perm_key):
                    return current_user
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permissão insuficiente",
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissão insuficiente",
        )
    return checker
