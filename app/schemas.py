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


class WorklogCreate(BaseModel):
    hours: float = Field(gt=0)
    author: str = Field(min_length=1, max_length=80)
    note: str = Field(default="", max_length=500)


class WorklogOut(BaseModel):
    id: int
    hours: float
    author: str
    note: str
    created_at: datetime


class TicketCreate(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    description: str = Field(default="", max_length=2000)
    priority: Priority = Priority.MEDIUM
    assignee: str | None = Field(default=None, max_length=80)
    project_id: int | None = None


class TicketUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    priority: Priority | None = None
    assignee: str | None = Field(default=None, max_length=80)


class TicketStatusChange(BaseModel):
    status: TicketStatus


class TicketAssign(BaseModel):
    username: str | None = Field(default=None, max_length=80)


class TicketProjectChange(BaseModel):
    project_id: int | None = None


class TicketOut(BaseModel):
    id: int
    title: str
    description: str
    status: TicketStatus
    priority: Priority
    assignee: str | None
    project_id: int | None
    label_ids: list[int]
    comments: list[CommentOut]
    worklogs: list[WorklogOut]
    due_at: datetime | None
    overdue: bool = False
    created_at: datetime
    updated_at: datetime


class MemberCreate(BaseModel):
    username: str = Field(min_length=2, max_length=32)
    display_name: str = Field(min_length=1, max_length=80)


class MemberOut(BaseModel):
    id: int
    username: str
    display_name: str
    active: bool
    created_at: datetime


class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    slug: str | None = Field(default=None, max_length=40)


class ProjectOut(BaseModel):
    id: int
    name: str
    slug: str
    archived: bool
    created_at: datetime


class LabelCreate(BaseModel):
    name: str = Field(min_length=1, max_length=40)
    slug: str | None = Field(default=None, max_length=40)


class LabelOut(BaseModel):
    id: int
    name: str
    slug: str


class BoardStatsOut(BaseModel):
    total_tickets: int
    by_status: dict[str, int]
    overdue: int
    hours_logged: float
    active_members: int
    open_projects: int


class HealthOut(BaseModel):
    status: str
    service: str
