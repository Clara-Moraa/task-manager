# main.py
# REST API for the workboard task manager
# FastAPI + SQLAlchemy + SQLite

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, validator
from datetime import datetime
from typing import Optional, List

from database import SessionLocal, TaskItem, Base, engine

app = FastAPI(title="Workboard API", version="1.0.0")

# allow the frontend (running on a different port) to hit this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Schemas ─────────────────────────────────────────────────────────────────

VALID_STATUSES = {"pending", "in_progress", "completed"}

class NewTask(BaseModel):
    title: str
    notes: Optional[str] = None
    progress: Optional[str] = "pending"
    deadline: Optional[datetime] = None

    @validator("title")
    def title_must_exist(cls, v):
        if not v or not v.strip():
            raise ValueError("title cannot be blank")
        return v.strip()

    @validator("progress")
    def progress_must_be_valid(cls, v):
        if v not in VALID_STATUSES:
            raise ValueError(f"progress must be one of: {', '.join(VALID_STATUSES)}")
        return v


class EditTask(BaseModel):
    title: Optional[str] = None
    notes: Optional[str] = None
    progress: Optional[str] = None
    deadline: Optional[datetime] = None

    @validator("progress", pre=True, always=True)
    def check_progress(cls, v):
        if v is not None and v not in VALID_STATUSES:
            raise ValueError(f"progress must be one of: {', '.join(VALID_STATUSES)}")
        return v


class TaskOut(BaseModel):
    id: int
    title: str
    notes: Optional[str]
    progress: str
    added_on: datetime
    deadline: Optional[datetime]

    class Config:
        orm_mode = True


# ── DB session helper ────────────────────────────────────────────────────────

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def fetch_task_or_404(task_id: int, db: Session) -> TaskItem:
    task = db.query(TaskItem).filter(TaskItem.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail=f"No task with id {task_id}")
    return task


# ── Routes ───────────────────────────────────────────────────────────────────

@app.post("/api/tasks", response_model=TaskOut, status_code=201)
def create_task(payload: NewTask, db: Session = Depends(get_db)):
    task = TaskItem(
        title    = payload.title,
        notes    = payload.notes,
        progress = payload.progress,
        deadline = payload.deadline,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@app.get("/api/tasks", response_model=List[TaskOut])
def get_all_tasks(db: Session = Depends(get_db)):
    return db.query(TaskItem).order_by(TaskItem.added_on.desc()).all()


@app.get("/api/tasks/{task_id}", response_model=TaskOut)
def get_single_task(task_id: int, db: Session = Depends(get_db)):
    return fetch_task_or_404(task_id, db)


@app.put("/api/tasks/{task_id}", response_model=TaskOut)
def update_task(task_id: int, payload: EditTask, db: Session = Depends(get_db)):
    task = fetch_task_or_404(task_id, db)
    changes = payload.dict(exclude_unset=True)
    for field, value in changes.items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


@app.delete("/api/tasks/{task_id}", status_code=204)
def remove_task(task_id: int, db: Session = Depends(get_db)):
    task = fetch_task_or_404(task_id, db)
    db.delete(task)
    db.commit()