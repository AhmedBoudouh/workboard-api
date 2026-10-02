from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session
from collections.abc import Generator
from config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


Base.metadata.create_all(engine)
