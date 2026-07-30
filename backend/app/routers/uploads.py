import os
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import require_role
from app.core.config import settings
from app.models import User, School

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("/school/{school_id}/photo", status_code=status.HTTP_200_OK)
def upload_school_photo(
    school_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("super_admin", "school_admin", module=None)),
):
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="Escola não encontrada")

    if current_user.role == "school_admin" and school.id != current_user.school_id:
        raise HTTPException(status_code=403, detail="Permissão insuficiente")

    allowed_types = {"image/jpeg", "image/png", "image/jpg", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Apenas imagens PNG, JPG ou WEBP são permitidas")

    ext = file.filename.split(".")[-1].lower()
    if ext not in {"png", "jpg", "jpeg", "webp"}:
        ext = "png"

    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    filename = f"school_{school_id}_{uuid.uuid4().hex}.{ext}"
    file_path = upload_dir / filename

    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    contents = file.file.read()
    if len(contents) > max_size:
        raise HTTPException(status_code=400, detail=f"Imagem deve ter no máximo {settings.MAX_UPLOAD_SIZE_MB}MB")

    with open(file_path, "wb") as f:
        f.write(contents)

    photo_url = f"/static/uploads/{filename}"
    school.photo_url = photo_url
    db.commit()

    return {"photo_url": photo_url}


@router.delete("/school/{school_id}/photo", status_code=status.HTTP_204_NO_CONTENT)
def remove_school_photo(
    school_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("super_admin", "school_admin", module=None)),
):
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="Escola não encontrada")

    if current_user.role == "school_admin" and school.id != current_user.school_id:
        raise HTTPException(status_code=403, detail="Permissão insuficiente")

    if school.photo_url:
        old_path = Path("../frontend") / school.photo_url.lstrip("/static/")
        try:
            if old_path.exists():
                old_path.unlink()
        except Exception:
            pass
        school.photo_url = None
        db.commit()
    return None
