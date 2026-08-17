#!/usr/bin/env python3
"""
Regenera os payloads QR de todos os alunos ativos.

Uso:
    cd /home/arisimoes/siscares/backend
    sudo .venv/bin/python scripts/regenerate_qr_codes.py
"""
import sys

sys.path.insert(0, ".")

from app.db.session import SessionLocal
from app.models import Student
from app.services.qr_service import generate_encrypted_qr_payload


def main():
    db = SessionLocal()
    try:
        students = (
            db.query(Student)
            .filter(Student.is_active == True)
            .filter(Student.is_transferred_externally == False)
            .all()
        )

        if not students:
            print("Nenhum aluno ativo encontrado.")
            return

        for student in students:
            student.encrypted_qr_payload = generate_encrypted_qr_payload(
                student, minimal_payload=True
            )

        db.commit()

        print(f"Regenerados {len(students)} QR code(s).")
        for student in students[:5]:
            print(
                f"  id={student.id} | {student.full_name[:35]:35} | "
                f"len={len(student.encrypted_qr_payload)} | "
                f"preview={student.encrypted_qr_payload[:50]}..."
            )
    finally:
        db.close()


if __name__ == "__main__":
    main()
