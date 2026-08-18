from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models import Module

CORE_MODULES = [
    ("core", "Gestão Escolar", "Cadastros de escolas, turmas, alunos, turnos e usuários", True),
    ("cards", "Carteirinhas", "Emissão de carteirinhas com QR Code criptografado", False),
    ("attendance", "Portaria / Chamada QR Code", "Registro de presença via leitura de QR Code", False),
    ("reports", "Relatórios de Frequência", "Relatórios mensais de frequência por turma", False),
    ("transfers", "Histórico de Transferências", "Transferências internas e externas de alunos", False),
    ("calendar", "Calendário", "Módulo reservado para funcionalidades futuras de calendário escolar", False),
    ("logs", "Registros", "Auditoria de transferências e justificativas de faltas", False),
    ("migration", "Migração de Alunos", "Migração de alunos entre anos letivos e turmas", False),
]


def seed_modules():
    db: Session = SessionLocal()
    try:
        for code, name, description, is_core in CORE_MODULES:
            existing = db.query(Module).filter(Module.code == code).first()
            if not existing:
                db.add(Module(code=code, name=name, description=description, is_core=is_core))
        db.commit()
    finally:
        db.close()
