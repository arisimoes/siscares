#!/usr/bin/env python3
"""
Script utilitário para criar o super-admin do SisCares.
Usage:
    python scripts/create_superadmin.py --email admin@siscares.local --password admin123 --name "Administrador"
"""
import argparse
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db.session import SessionLocal
from app.services.auth_service import create_user


def main():
    parser = argparse.ArgumentParser(description="Cria super-admin do SisCares")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--name", default="Super Admin")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        user = create_user(db, email=args.email, password=args.password, full_name=args.name, role="super_admin")
        print(f"Super admin criado: {user.email} (id={user.id})")
    except Exception as e:
        print(f"Erro: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
