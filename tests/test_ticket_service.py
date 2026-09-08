import pytest

from app.exceptions import InvalidStatusTransition, TicketClosedError, TicketNotFound
from app.models import Priority, TicketStatus
from app.services.ticket_service import TicketService


def test_list_tickets_can_filter_by_status(service: TicketService) -> None:
    open_tickets = service.list_tickets(status=TicketStatus.OPEN)
    assert all(ticket.status == TicketStatus.OPEN for ticket in open_tickets)
    assert len(open_tickets) == 1


def test_create_ticket_strips_whitespace(service: TicketService) -> None:
    ticket = service.create_ticket(title="  New bug  ", description="  overflow  ")
    assert ticket.title == "New bug"
    assert ticket.description == "overflow"
    assert ticket.status == TicketStatus.OPEN


def test_change_status_follows_allowed_path(service: TicketService) -> None:
    ticket = service.create_ticket(title="Move me")
    service.change_status(ticket.id, TicketStatus.IN_PROGRESS)
    service.change_status(ticket.id, TicketStatus.RESOLVED)
    closed = service.change_status(ticket.id, TicketStatus.CLOSED)
    assert closed.status == TicketStatus.CLOSED


def test_change_status_rejects_skip(service: TicketService) -> None:
    ticket = service.create_ticket(title="Skip path")
    with pytest.raises(InvalidStatusTransition):
        service.change_status(ticket.id, TicketStatus.CLOSED)


def test_cannot_update_or_comment_closed_ticket(service: TicketService) -> None:
    ticket = service.create_ticket(title="Lock me")
    service.change_status(ticket.id, TicketStatus.IN_PROGRESS)
    service.change_status(ticket.id, TicketStatus.RESOLVED)
    service.change_status(ticket.id, TicketStatus.CLOSED)

    with pytest.raises(TicketClosedError):
        service.update_ticket(ticket.id, priority=Priority.HIGH)
    with pytest.raises(TicketClosedError):
        service.add_comment(ticket.id, "too late", "maya")
    with pytest.raises(TicketClosedError):
        service.delete_ticket(ticket.id)


def test_get_unknown_ticket_raises(service: TicketService) -> None:
    with pytest.raises(TicketNotFound):
        service.get_ticket(999)
