from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.core.security import require_role, get_current_user
from app.models import User, UserPermission
from app.schemas import LoginRequest, Token, UserCreate, UserResponse, UserUpdate, UserPermissionCreate
from app.services.auth_service import authenticate_user, create_access_token, create_user

router = APIRouter(prefix="/auth", tags=["auth"])


def _apply_user_update(db, user: User, payload: UserUpdate):
    data = payload.model_dump(exclude_unset=True)
    # Ao atualizar senha, hashear
    if "password" in data and data["password"]:
        from app.services.auth_service import get_password_hash
        user.hashed_password = get_password_hash(data.pop("password"))
    elif "password" in data:
        data.pop("password")

    # Atualizar permissões se presentes e não for gestor
    if "permissions" in data and user.role != "school_admin":
        perm_data = data.pop("permissions")
        perm = db.query(UserPermission).filter(UserPermission.user_id == user.id).first()
        if not perm:
            perm = UserPermission(user_id=user.id)
            db.add(perm)
        for field, value in perm_data.items():
            setattr(perm, field, value)
        db.flush()

    for field, value in data.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(form_data: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.login, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas")
    token = create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/users", response_model=UserResponse)
def create_new_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("school_admin", "secretary", module="users")),
):
    # Super_admin não utiliza este endpoint; gestores têm endpoint próprio
    if current_user.role == "super_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Super admin deve utilizar o endpoint de gestores")
    # Apenas gestores escolares administram funcionários da própria escola
    if payload.school_id != current_user.school_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissão insuficiente")
    # Gestores e secretários só podem criar papéis de funcionários (nunca gestores ou super_admin)
    if payload.role in {"super_admin", "school_admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Não pode cadastrar gestores")
    user = create_user(
        db,
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
        role=payload.role,
        school_id=payload.school_id,
    )
    # Se houver permissões no payload, salvar permissões
    if payload.permissions:
        perm_data = payload.permissions.model_dump()
        perm = UserPermission(user_id=user.id, **perm_data)
        db.add(perm)
        db.commit()
        db.refresh(user)
    return user


@router.post("/managers", response_model=UserResponse)
def create_manager(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("super_admin")),
):
    if payload.role not in {"school_admin"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Este endpoint é exclusivo para gestores escolares")
    user = create_user(
        db,
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
        role=payload.role,
        school_id=payload.school_id,
    )
    return user


@router.get("/managers", response_model=List[UserResponse])
def list_managers(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("super_admin")),
):
    return db.query(User).filter(User.role == "school_admin").all()


@router.get("/users", response_model=List[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("school_admin", "secretary", module="users")),
):
    # Lista apenas funcionários (staff/secretary) da própria escola
    query = db.query(User).filter(User.role.in_({"staff", "secretary"}))
    if current_user.role in {"school_admin", "secretary"}:
        query = query.filter(User.school_id == current_user.school_id)
    return query.all()


@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("school_admin", "secretary", module="users")),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    if current_user.role in {"school_admin", "secretary"} and user.school_id != current_user.school_id:
        raise HTTPException(status_code=403, detail="Permissão insuficiente")
    if user.role in {"super_admin", "school_admin"}:
        raise HTTPException(status_code=403, detail="Não pode alterar gestores por este endpoint")
    if current_user.role == "secretary" and user.role in {"super_admin", "school_admin"}:
        raise HTTPException(status_code=403, detail="Permissão insuficiente")

    return _apply_user_update(db, user, payload)


@router.put("/managers/{user_id}", response_model=UserResponse)
def update_manager(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("super_admin")),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    if user.role != "school_admin":
        raise HTTPException(status_code=403, detail="Este endpoint é exclusivo para gestores escolares")

    return _apply_user_update(db, user, payload)
