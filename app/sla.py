from datetime import datetime, timedelta

from app.models import Priority, Ticket, TicketStatus, utc_now

SLA_HOURS: dict[Priority, int] = {
    Priority.HIGH: 8,
    Priority.MEDIUM: 24,
    Priority.LOW: 72,
}

TERMINAL_STATUSES = {TicketStatus.RESOLVED, TicketStatus.CLOSED}


def due_at_for(created_at: datetime, priority: Priority) -> datetime:
    """SLA clock starts at created_at and depends only on current priority."""
    return created_at + timedelta(hours=SLA_HOURS[priority])


def is_overdue(ticket: Ticket, now: datetime | None = None) -> bool:
    if ticket.status in TERMINAL_STATUSES:
        return False
    if ticket.due_at is None:
        return False
    moment = now or utc_now()
    return moment > ticket.due_at


def remaining_hours(ticket: Ticket, now: datetime | None = None) -> float:
    if ticket.due_at is None:
        return 0.0
    moment = now or utc_now()
    delta = (ticket.due_at - moment).total_seconds() / 3600
    return round(delta, 2)


def hours_logged(ticket: Ticket) -> float:
    return round(sum(item.hours for item in ticket.worklogs), 2)
