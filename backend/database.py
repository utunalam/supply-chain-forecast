
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Store the database beside this file.
DATABASE_PATH = Path(__file__).resolve().parent / "supply_chain.db"

# Convert the file path into a SQLite connection URL.
DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"

# Create the SQLAlchemy engine.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Create a session factory.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for SQLAlchemy database models.
Base = declarative_base()


# Provide a database session to the application.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
