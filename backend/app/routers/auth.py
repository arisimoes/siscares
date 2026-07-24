from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.core.security import require_role, get_current_user
from app.models import User, UserPermission
from app.schemas import LoginRequest, Token, UserCreate, UserResponse, UserUpdate, UserPermissionCreate
from app.services.auth_service import authenticate_user, create_access_token, create_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(form_data: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
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
    current_user: User = Depends(require_role("super_admin", "school_admin", "secretary", module="users")),
):
    # school_admin só pode criar usuários da própria escola
    if current_user.role == "school_admin" and payload.school_id != current_user.school_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissão insuficiente")
    user = create_user(
        db,
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
        role=payload.role,
        school_id=payload.school_id,
    )
    # Se houver permissões no payload e não for gestor, salvar permissões
    if payload.permissions and payload.role != "school_admin":
        perm_data = payload.permissions.model_dump()
        perm = UserPermission(user_id=user.id, **perm_data)
        db.add(perm)
        db.commit()
        db.refresh(user)
    return user


@router.get("/users", response_model=List[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("super_admin", "school_admin", "secretary", module="users")),
):
    query = db.query(User)
    if current_user.role == "school_admin":
        query = query.filter(User.school_id == current_user.school_id)
    return query.all()


@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("super_admin", "school_admin", "secretary", module="users")),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    if current_user.role == "school_admin" and user.school_id != current_user.school_id:
        raise HTTPException(status_code=403, detail="Permissão insuficiente")
    if current_user.role == "school_admin" and user.role == "super_admin":
        raise HTTPException(status_code=403, detail="Não pode alterar super admin")
    if current_user.role == "secretary" and (user.school_id != current_user.school_id or user.role in {"super_admin", "school_admin"}):
        raise HTTPException(status_code=403, detail="Permissão insuficiente")


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
