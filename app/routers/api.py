from fastapi import APIRouter, Depends, Query, status

from app.deps import get_label_service, get_ticket_service, get_worklog_service
from app.exceptions import DeskError, TicketNotFound
from app.http_errors import http_error
from app.models import Priority, Ticket, TicketStatus
from app.schemas import (
    CommentCreate,
    CommentOut,
    HealthOut,
    TicketAssign,
    TicketCreate,
    TicketOut,
    TicketProjectChange,
    TicketStatusChange,
    TicketUpdate,
    WorklogCreate,
    WorklogOut,
)
from app.services.label_service import LabelService
from app.services.ticket_service import TicketService
from app.services.worklog_service import WorklogService
from app.sla import is_overdue

router = APIRouter(tags=["tickets"])


def to_ticket_out(ticket: Ticket) -> TicketOut:
    payload = TicketOut.model_validate(ticket, from_attributes=True)
    return payload.model_copy(update={"overdue": is_overdue(ticket)})


@router.get("/health", response_model=HealthOut, tags=["health"])
def health() -> HealthOut:
    return HealthOut(status="ok", service="desk")


@router.get("/tickets", response_model=list[TicketOut])
def list_tickets(
    status_filter: TicketStatus | None = Query(default=None, alias="status"),
    priority: Priority | None = None,
    project_id: int | None = None,
    q: str | None = None,
    overdue: bool | None = None,
    service: TicketService = Depends(get_ticket_service),
) -> list[TicketOut]:
    tickets = service.list_tickets(status_filter, priority, project_id, q, overdue)
    return [to_ticket_out(ticket) for ticket in tickets]


@router.post("/tickets", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
def create_ticket(
    payload: TicketCreate,
    service: TicketService = Depends(get_ticket_service),
) -> TicketOut:
    try:
        ticket = service.create_ticket(
            title=payload.title,
            description=payload.description,
            priority=payload.priority,
            assignee=payload.assignee,
            project_id=payload.project_id,
        )
        return to_ticket_out(ticket)
    except DeskError as exc:
        raise http_error(exc) from exc


@router.get("/tickets/{ticket_id}", response_model=TicketOut)
def get_ticket(
    ticket_id: int,
    service: TicketService = Depends(get_ticket_service),
) -> TicketOut:
    try:
        return to_ticket_out(service.get_ticket(ticket_id))
    except TicketNotFound as exc:
        raise http_error(exc) from exc


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
        return to_ticket_out(ticket)
    except DeskError as exc:
        raise http_error(exc) from exc


@router.post("/tickets/{ticket_id}/status", response_model=TicketOut)
def change_status(
    ticket_id: int,
    payload: TicketStatusChange,
    service: TicketService = Depends(get_ticket_service),
) -> TicketOut:
    try:
        return to_ticket_out(service.change_status(ticket_id, payload.status))
    except DeskError as exc:
        raise http_error(exc) from exc


@router.post("/tickets/{ticket_id}/assign", response_model=TicketOut)
def assign_ticket(
    ticket_id: int,
    payload: TicketAssign,
    service: TicketService = Depends(get_ticket_service),
) -> TicketOut:
    try:
        return to_ticket_out(service.assign(ticket_id, payload.username))
    except DeskError as exc:
        raise http_error(exc) from exc


@router.post("/tickets/{ticket_id}/project", response_model=TicketOut)
def set_ticket_project(
    ticket_id: int,
    payload: TicketProjectChange,
    service: TicketService = Depends(get_ticket_service),
) -> TicketOut:
    try:
        return to_ticket_out(service.set_project(ticket_id, payload.project_id))
    except DeskError as exc:
        raise http_error(exc) from exc


@router.delete("/tickets/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket(
    ticket_id: int,
    service: TicketService = Depends(get_ticket_service),
) -> None:
    try:
        service.delete_ticket(ticket_id)
    except DeskError as exc:
        raise http_error(exc) from exc


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
    except DeskError as exc:
        raise http_error(exc) from exc


@router.post(
    "/tickets/{ticket_id}/labels/{label_id}",
    response_model=TicketOut,
    status_code=status.HTTP_201_CREATED,
)
def attach_label(
    ticket_id: int,
    label_id: int,
    service: LabelService = Depends(get_label_service),
) -> TicketOut:
    try:
        return to_ticket_out(service.attach(ticket_id, label_id))
    except DeskError as exc:
        raise http_error(exc) from exc


@router.delete("/tickets/{ticket_id}/labels/{label_id}", response_model=TicketOut)
def detach_label(
    ticket_id: int,
    label_id: int,
    service: LabelService = Depends(get_label_service),
) -> TicketOut:
    try:
        return to_ticket_out(service.detach(ticket_id, label_id))
    except DeskError as exc:
        raise http_error(exc) from exc


@router.post(
    "/tickets/{ticket_id}/worklogs",
    response_model=WorklogOut,
    status_code=status.HTTP_201_CREATED,
)
def add_worklog(
    ticket_id: int,
    payload: WorklogCreate,
    service: WorklogService = Depends(get_worklog_service),
) -> WorklogOut:
    try:
        worklog = service.add_worklog(ticket_id, payload.hours, payload.author, payload.note)
        return WorklogOut.model_validate(worklog, from_attributes=True)
    except DeskError as exc:
        raise http_error(exc) from exc
