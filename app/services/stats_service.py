from collections import Counter

from app.models import TicketStatus
from app.schemas import BoardStatsOut
from app.sla import hours_logged, is_overdue
from app.store import InMemoryStore


class StatsService:
    def __init__(self, store: InMemoryStore) -> None:
        self.store = store

    def summarize(self) -> BoardStatsOut:
        tickets = self.store.list_all()
        by_status = Counter(ticket.status.value for ticket in tickets)
        return BoardStatsOut(
            total_tickets=len(tickets),
            by_status={status.value: by_status.get(status.value, 0) for status in TicketStatus},
            overdue=sum(1 for ticket in tickets if is_overdue(ticket)),
            hours_logged=round(sum(hours_logged(ticket) for ticket in tickets), 2),
            active_members=sum(1 for member in self.store.list_members() if member.active),
            open_projects=sum(1 for project in self.store.list_projects() if not project.archived),
        )
