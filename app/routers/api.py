from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.deps import get_ticket_service
from app.exceptions import InvalidStatusTransition, TicketClosedError, TicketNotFound
from app.models import Priority, Ticket, TicketStatus
from app.schemas import (
    CommentCreate,
    CommentOut,
    HealthOut,
    TicketCreate,
    TicketOut,
    TicketStatusChange,
    TicketUpdate,
)
from app.services.ticket_service import TicketService

router = APIRouter()


def _to_out(ticket: Ticket) -> TicketOut:
    return TicketOut.model_validate(ticket, from_attributes=True)


def _http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, TicketNotFound):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, (InvalidStatusTransition, TicketClosedError)):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    raise exc


@router.get("/health", response_model=HealthOut)
def health() -> HealthOut:
    return HealthOut(status="ok", service="desk")


@router.get("/tickets", response_model=list[TicketOut])
def list_tickets(
    status_filter: TicketStatus | None = Query(default=None, alias="status"),
    priority: Priority | None = None,
    service: TicketService = Depends(get_ticket_service),
) -> list[TicketOut]:
    return [_to_out(ticket) for ticket in service.list_tickets(status_filter, priority)]


@router.post("/tickets", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
def create_ticket(
    payload: TicketCreate,
    service: TicketService = Depends(get_ticket_service),
) -> TicketOut:
    ticket = service.create_ticket(
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        assignee=payload.assignee,
    )
    return _to_out(ticket)


@router.get("/tickets/{ticket_id}", response_model=TicketOut)
def get_ticket(
    ticket_id: int,
    service: TicketService = Depends(get_ticket_service),
) -> TicketOut:
    try:
        return _to_out(service.get_ticket(ticket_id))
    except TicketNotFound as exc:
        raise _http_error(exc) from exc


@router.patch("/tickets/{ticket_id}", response_model=TicketOut)
def update_ticket(
    ticket_id: int,
    payload: TicketUpdate,
    service: TicketService = Depends(get_ticket_service),
) -> TicketOut:
    try:
        ticket = service.update_ticket(
            ticket_id,
            title=payload.title,
            description=payload.description,
            priority=payload.priority,
            assignee=payload.assignee,
        )
        return _to_out(ticket)
    except (TicketNotFound, TicketClosedError) as exc:
        raise _http_error(exc) from exc


@router.post("/tickets/{ticket_id}/status", response_model=TicketOut)
def change_status(
    ticket_id: int,
    payload: TicketStatusChange,
    service: TicketService = Depends(get_ticket_service),
) -> TicketOut:
    try:
        return _to_out(service.change_status(ticket_id, payload.status))
    except (TicketNotFound, InvalidStatusTransition) as exc:
        raise _http_error(exc) from exc


@router.delete("/tickets/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket(
    ticket_id: int,
    service: TicketService = Depends(get_ticket_service),
) -> None:
    try:
        service.delete_ticket(ticket_id)
    except (TicketNotFound, TicketClosedError) as exc:
        raise _http_error(exc) from exc


@router.post(
    "/tickets/{ticket_id}/comments",
    response_model=CommentOut,
    status_code=status.HTTP_201_CREATED,
)
def add_comment(
    ticket_id: int,
    payload: CommentCreate,
    service: TicketService = Depends(get_ticket_service),
) -> CommentOut:
    try:
        comment = service.add_comment(ticket_id, payload.body, payload.author)
        return CommentOut.model_validate(comment, from_attributes=True)
    except (TicketNotFound, TicketClosedError) as exc:
        raise _http_error(exc) from exc
