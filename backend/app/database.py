"""SQLAlchemy sessions shared by HTTP and bounded job workers."""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models import Base


def make_engine(url: str):
    options = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False, "timeout": 30}
    result = create_engine(url, **options)
    if url.startswith("sqlite"):

        @event.listens_for(result, "connect")
        def sqlite_foreign_keys(connection, _):
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return result


engine = make_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    with SessionLocal() as db:
        try:
            yield db
        except Exception:
            db.rollback()
            raise


def create_schema():
    """Local convenience only; deployment uses Alembic migrations."""
    Base.metadata.create_all(engine)
