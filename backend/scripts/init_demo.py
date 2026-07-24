#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db.session import SessionLocal
from app.services.auth_service import create_user, get_or_create_school


def main():
    db = SessionLocal()
    try:
        # Cria escola padrão
        school = get_or_create_school(db, "Escola Modelo")
        print(f"Escola criada: {school.name} (id={school.id})")

        # Cria super-admin se não existir
        from app.models import User
        admin = db.query(User).filter(User.email == "admin@siscares.local").first()
        if not admin:
            admin = create_user(db, "admin@siscares.local", "admin123", "Super Admin", "super_admin")
            print(f"Super admin criado: {admin.email} (id={admin.id})")

        # Habilita todos os módulos para a escola modelo
        from app.models import Module, SchoolModuleSetting
        modules = db.query(Module).all()
        for module in modules:
            setting = db.query(SchoolModuleSetting).filter(
                SchoolModuleSetting.school_id == school.id,
                SchoolModuleSetting.module_id == module.id,
            ).first()
            if not setting:
                db.add(SchoolModuleSetting(school_id=school.id, module_id=module.id, is_enabled=True))
        db.commit()
        print("Módulos habilitados para a escola modelo")

        # Cria turnos de exemplo
        from app.models import Shift
        if not db.query(Shift).filter(Shift.school_id == school.id).first():
            db.add_all([
                Shift(school_id=school.id, name="Matutino", start_time="07:00", end_time="12:00"),
                Shift(school_id=school.id, name="Vespertino", start_time="13:00", end_time="17:30"),
                Shift(school_id=school.id, name="Noturno", start_time="18:30", end_time="22:00"),
            ])
            db.commit()
            print("Turnos de exemplo criados")

        # Cria turma de exemplo
        from app.models import Class
        if not db.query(Class).filter(Class.school_id == school.id).first():
            cls = Class(school_id=school.id, name="1º Ano A", grade="1º ano", year=2026)
            db.add(cls)
            db.commit()
            print(f"Turma criada: {cls.name} (id={cls.id})")

    except Exception as e:
        print(f"Erro: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
