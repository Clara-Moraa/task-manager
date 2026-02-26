# database.py
# Setting up SQLite via SQLAlchemy — keeping it simple, no need to spin up Postgres for this

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DB_FILE = "sqlite:///./workboard.db"

engine = create_engine(DB_FILE, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


class TaskItem(Base):
    __tablename__ = "task_items"

    id          = Column(Integer, primary_key=True, index=True)
    title       = Column(String(255), nullable=False, index=True)
    notes       = Column(Text, nullable=True)
    progress    = Column(String(30), default="pending")   # pending | in_progress | completed
    added_on    = Column(DateTime, default=datetime.utcnow)
    deadline    = Column(DateTime, nullable=True)


# run once to create the table if it doesn't exist
Base.metadata.create_all(bind=engine)