from app.exceptions import (
    InvalidStatusTransition,
    MemberInactiveError,
    MemberNotFound,
    ProjectArchivedError,
    ProjectNotFound,
    TicketClosedError,
    TicketNotFound,
)
from app.models import Comment, Priority, Ticket, TicketStatus, utc_now
from app.sla import due_at_for, is_overdue
from app.store import InMemoryStore

ALLOWED_TRANSITIONS: dict[TicketStatus, set[TicketStatus]] = {
    TicketStatus.OPEN: {TicketStatus.IN_PROGRESS},
    TicketStatus.IN_PROGRESS: {TicketStatus.OPEN, TicketStatus.RESOLVED},
    TicketStatus.RESOLVED: {TicketStatus.IN_PROGRESS, TicketStatus.CLOSED},
    TicketStatus.CLOSED: set(),
}

ACTIVE_STATUSES = {TicketStatus.OPEN, TicketStatus.IN_PROGRESS}


class TicketService:
    def __init__(self, store: InMemoryStore) -> None:
        self.store = store

    def list_tickets(
        self,
        status: TicketStatus | None = None,
        priority: Priority | None = None,
        project_id: int | None = None,
        q: str | None = None,
        overdue: bool | None = None,
    ) -> list[Ticket]:
        tickets = self.store.list_all()
        if status is not None:
            tickets = [ticket for ticket in tickets if ticket.status == status]
        if priority is not None:
            tickets = [ticket for ticket in tickets if ticket.priority == priority]
        if project_id is not None:
            tickets = [ticket for ticket in tickets if ticket.project_id == project_id]
        if q:
            needle = q.strip().lower()
            tickets = [
                ticket
                for ticket in tickets
                if needle in ticket.title.lower()
                or needle in ticket.description.lower()
                or needle in (ticket.assignee or "")
            ]
        if overdue is True:
            tickets = [ticket for ticket in tickets if is_overdue(ticket)]
        elif overdue is False:
            tickets = [ticket for ticket in tickets if not is_overdue(ticket)]
        return sorted(tickets, key=lambda ticket: ticket.id)

    def get_ticket(self, ticket_id: int) -> Ticket:
        ticket = self.store.get(ticket_id)
        if ticket is None:
            raise TicketNotFound(ticket_id)
        return ticket

    def create_ticket(
        self,
        title: str,
        description: str = "",
        priority: Priority = Priority.MEDIUM,
        assignee: str | None = None,
        project_id: int | None = None,
    ) -> Ticket:
        resolved_assignee = self._resolve_assignee(assignee)
        resolved_project_id = self._resolve_project_id(project_id)
        return self.store.create_ticket(
            title=title.strip(),
            description=description.strip(),
            priority=priority,
            assignee=resolved_assignee,
            project_id=resolved_project_id,
        )

    def update_ticket(
        self,
        ticket_id: int,
        title: str | None = None,
        description: str | None = None,
        priority: Priority | None = None,
        assignee: str | None = None,
    ) -> Ticket:
        ticket = self.get_ticket(ticket_id)
        self._ensure_not_closed(ticket, "update")
        if title is not None:
            ticket.title = title.strip()
        if description is not None:
            ticket.description = description.strip()
        if priority is not None:
            ticket.priority = priority
            ticket.due_at = due_at_for(ticket.created_at, ticket.priority)
        if assignee is not None:
            ticket.assignee = self._resolve_assignee(assignee)
        ticket.updated_at = utc_now()
        return ticket

    def change_status(self, ticket_id: int, target: TicketStatus) -> Ticket:
        ticket = self.get_ticket(ticket_id)
        if target == ticket.status:
            return ticket
        allowed = ALLOWED_TRANSITIONS[ticket.status]
        if target not in allowed:
            raise InvalidStatusTransition(ticket.status, target)
        ticket.status = target
        ticket.updated_at = utc_now()
        return ticket

    def delete_ticket(self, ticket_id: int) -> None:
        ticket = self.get_ticket(ticket_id)
        self._ensure_not_closed(ticket, "delete")
        self.store.delete(ticket_id)

    def add_comment(self, ticket_id: int, body: str, author: str) -> Comment:
        ticket = self.get_ticket(ticket_id)
        self._ensure_not_closed(ticket, "comment on")
        return ticket.add_comment(body=body.strip(), author=author.strip())

    def assign(self, ticket_id: int, username: str | None) -> Ticket:
        ticket = self.get_ticket(ticket_id)
        self._ensure_not_closed(ticket, "assign")
        ticket.assignee = self._resolve_assignee(username)
        ticket.updated_at = utc_now()
        return ticket

    def set_project(self, ticket_id: int, project_id: int | None) -> Ticket:
        ticket = self.get_ticket(ticket_id)
        self._ensure_not_closed(ticket, "move")
        ticket.project_id = self._resolve_project_id(project_id)
        ticket.updated_at = utc_now()
        return ticket

    def _resolve_assignee(self, username: str | None) -> str | None:
        if not username or not username.strip():
            return None
        member = self.store.get_member_by_username(username.strip())
        if member is None:
            raise MemberNotFound(username.strip())
        if not member.active:
            raise MemberInactiveError(member.username)
        return member.username

    def _resolve_project_id(self, project_id: int | None) -> int | None:
        if project_id is None:
            return None
        project = self.store.get_project(project_id)
        if project is None:
            raise ProjectNotFound(project_id)
        if project.archived:
            raise ProjectArchivedError(project_id, "attach ticket to")
        return project.id

    @staticmethod
    def _ensure_not_closed(ticket: Ticket, action: str) -> None:
        if ticket.status == TicketStatus.CLOSED:
            raise TicketClosedError(ticket.id, action)
