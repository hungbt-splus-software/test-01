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
class Comment:
    id: int
    body: str
    author: str
    created_at: datetime = field(default_factory=utc_now)


@dataclass
class Ticket:
    id: int
    title: str
    description: str
    status: TicketStatus = TicketStatus.OPEN
    priority: Priority = Priority.MEDIUM
    assignee: str | None = None
    comments: list[Comment] = field(default_factory=list)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    _next_comment_id: int = field(default=1, repr=False)

    def add_comment(self, body: str, author: str) -> Comment:
        comment = Comment(id=self._next_comment_id, body=body, author=author)
        self._next_comment_id += 1
        self.comments.append(comment)
        self.updated_at = utc_now()
        return comment
