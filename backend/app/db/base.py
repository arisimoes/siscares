from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def ensure_schema():
    from app import models  # noqa: F401
    Base.metadata.create_all(bind=engine)


def ensure_column_exists(table_name: str, column_name: str, column_type):
    """Adiciona uma coluna se ela ainda não existir no banco (fallback sem alembic)."""
    from sqlalchemy import inspect, text
    insp = inspect(engine)
    if table_name in insp.get_table_names() and column_name not in [c["name"] for c in insp.get_columns(table_name)]:
        with engine.connect() as conn:
            conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"))
            conn.commit()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
