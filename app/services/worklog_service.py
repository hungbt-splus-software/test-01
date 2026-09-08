from app.constants import MAX_TICKET_HOURS, MAX_WORKLOG_HOURS
from app.exceptions import InvalidWorklogError, TicketClosedError, TicketNotFound, WorklogLimitError
from app.models import Ticket, TicketStatus, Worklog
from app.sla import hours_logged
from app.store import InMemoryStore


class WorklogService:
    def __init__(self, store: InMemoryStore) -> None:
        self.store = store

    def add_worklog(
        self,
        ticket_id: int,
        hours: float,
        author: str,
        note: str = "",
    ) -> Worklog:
        ticket = self._get_writable_ticket(ticket_id)
        if hours <= 0 or hours > MAX_WORKLOG_HOURS:
            raise InvalidWorklogError(hours)
        total = hours_logged(ticket) + hours
        if total > MAX_TICKET_HOURS:
            raise WorklogLimitError(ticket.id, total, MAX_TICKET_HOURS)
        return ticket.add_worklog(hours, author.strip(), note.strip())

    def _get_writable_ticket(self, ticket_id: int) -> Ticket:
        ticket = self.store.get(ticket_id)
        if ticket is None:
            raise TicketNotFound(ticket_id)
        if ticket.status == TicketStatus.CLOSED:
            raise TicketClosedError(ticket.id, "log time on")
        return ticket
