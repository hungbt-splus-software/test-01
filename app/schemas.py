from datetime import datetime

from pydantic import BaseModel, Field

from app.models import Priority, TicketStatus


class CommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=500)
    author: str = Field(min_length=1, max_length=80)


class CommentOut(BaseModel):
    id: int
    body: str
    author: str
    created_at: datetime


class TicketCreate(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    description: str = Field(default="", max_length=2000)
    priority: Priority = Priority.MEDIUM
    assignee: str | None = Field(default=None, max_length=80)


class TicketUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    priority: Priority | None = None
    assignee: str | None = Field(default=None, max_length=80)


class TicketStatusChange(BaseModel):
    status: TicketStatus


class TicketOut(BaseModel):
    id: int
    title: str
    description: str
    status: TicketStatus
    priority: Priority
    assignee: str | None
    comments: list[CommentOut]
    created_at: datetime
    updated_at: datetime


class HealthOut(BaseModel):
    status: str
    service: str
