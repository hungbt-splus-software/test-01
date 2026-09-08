from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TicketStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class Priority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class Member:
    id: int
    username: str
    display_name: str
    active: bool = True
    created_at: datetime = field(default_factory=utc_now)


@dataclass
class Project:
    id: int
    name: str
    slug: str
    archived: bool = False
    created_at: datetime = field(default_factory=utc_now)


@dataclass
class Label:
    id: int
    name: str
    slug: str


@dataclass
class Comment:
    id: int
    body: str
    author: str
    created_at: datetime = field(default_factory=utc_now)


@dataclass
class Worklog:
    id: int
    hours: float
    author: str
    note: str = ""
    created_at: datetime = field(default_factory=utc_now)


@dataclass
class Ticket:
    id: int
    title: str
    description: str
    status: TicketStatus = TicketStatus.OPEN
    priority: Priority = Priority.MEDIUM
    assignee: str | None = None
    project_id: int | None = None
    label_ids: list[int] = field(default_factory=list)
    comments: list[Comment] = field(default_factory=list)
    worklogs: list[Worklog] = field(default_factory=list)
    due_at: datetime | None = None
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    _next_comment_id: int = field(default=1, repr=False)
    _next_worklog_id: int = field(default=1, repr=False)

    def add_comment(self, body: str, author: str) -> Comment:
        comment = Comment(id=self._next_comment_id, body=body, author=author)
        self._next_comment_id += 1
        self.comments.append(comment)
        self.updated_at = utc_now()
        return comment

    def add_worklog(self, hours: float, author: str, note: str = "") -> Worklog:
        worklog = Worklog(
            id=self._next_worklog_id,
            hours=hours,
            author=author,
            note=note,
        )
        self._next_worklog_id += 1
        self.worklogs.append(worklog)
        self.updated_at = utc_now()
        return worklog
