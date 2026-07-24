from sqlalchemy.orm import Session
from typing import Optional
from app.models import User, School
from app.core.crypto import verify_password, hash_password
from app.core.security import settings
from datetime import datetime, timedelta
from jose import jwt


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(user_id: int, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": str(user_id), "exp": expire}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_user(db: Session, email: str, password: str, full_name: str, role: str, school_id: Optional[int] = None) -> User:
    hashed = hash_password(password)
    user = User(
        email=email,
        hashed_password=hashed,
        full_name=full_name,
        role=role,
        school_id=school_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_or_create_school(db: Session, name: str = "Escola Padrão") -> School:
    school = db.query(School).filter(School.name == name).first()
    if not school:
        school = School(name=name)
        db.add(school)
        db.commit()
        db.refresh(school)
    return school
