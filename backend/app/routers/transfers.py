from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_user, require_role
from app.models import User, Student, Class, TransferHistory
from app.schemas import TransferHistoryCreate, TransferHistoryResponse

router = APIRouter(prefix="/transfers", tags=["transfers"])


@router.post("", response_model=TransferHistoryResponse)
def register_transfer(
    payload: TransferHistoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("school_admin", "secretary", "staff", module="transfers")),
):
    student = db.query(Student).filter(Student.id == payload.student_id, Student.school_id == current_user.school_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")

    # Atualiza turma atual se for transferência interna com destino
    if payload.transfer_type == "internal" and payload.to_class_id:
        new_class = db.query(Class).filter(Class.id == payload.to_class_id, Class.school_id == current_user.school_id).first()
        if not new_class:
            raise HTTPException(status_code=404, detail="Turma de destino não encontrada")
        payload.from_class_id = student.class_id
        student.class_id = payload.to_class_id
        student.is_transferred_externally = False
    elif payload.transfer_type == "external":
        payload.from_class_id = student.class_id
        student.class_id = None
        student.is_transferred_externally = True

    transfer = TransferHistory(
        **payload.model_dump(),
        registered_by_user_id=current_user.id,
    )
    db.add(transfer)
    db.commit()
    db.refresh(transfer)
    db.refresh(student)
    return transfer


@router.get("/student/{student_id}", response_model=list[TransferHistoryResponse])
def list_transfers(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    student = db.query(Student).filter(Student.id == student_id, Student.school_id == current_user.school_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")
    return db.query(TransferHistory).filter(TransferHistory.student_id == student_id).all()
