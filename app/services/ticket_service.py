from app.exceptions import InvalidStatusTransition, TicketClosedError, TicketNotFound
from app.models import Comment, Priority, Ticket, TicketStatus, utc_now
from app.store import InMemoryStore

ALLOWED_TRANSITIONS: dict[TicketStatus, set[TicketStatus]] = {
    TicketStatus.OPEN: {TicketStatus.IN_PROGRESS},
    TicketStatus.IN_PROGRESS: {TicketStatus.OPEN, TicketStatus.RESOLVED},
    TicketStatus.RESOLVED: {TicketStatus.IN_PROGRESS, TicketStatus.CLOSED},
    TicketStatus.CLOSED: set(),
}


class TicketService:
    def __init__(self, store: InMemoryStore) -> None:
        self.store = store

    def list_tickets(
        self,
        status: TicketStatus | None = None,
        priority: Priority | None = None,
    ) -> list[Ticket]:
        tickets = self.store.list_all()
        if status is not None:
            tickets = [ticket for ticket in tickets if ticket.status == status]
        if priority is not None:
            tickets = [ticket for ticket in tickets if ticket.priority == priority]
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
    ) -> Ticket:
        return self.store.create_ticket(
            title=title.strip(),
            description=description.strip(),
            priority=priority,
            assignee=assignee.strip() if assignee else None,
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
        if assignee is not None:
            ticket.assignee = assignee.strip() or None
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

    @staticmethod
    def _ensure_not_closed(ticket: Ticket, action: str) -> None:
        if ticket.status == TicketStatus.CLOSED:
            raise TicketClosedError(ticket.id, action)
