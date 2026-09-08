from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.deps import get_ticket_service
from app.exceptions import InvalidStatusTransition, TicketClosedError, TicketNotFound
from app.models import Priority, TicketStatus
from app.services.ticket_service import TicketService

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))


@router.get("/", response_class=HTMLResponse)
def board(
    request: Request,
    service: TicketService = Depends(get_ticket_service),
):
    tickets = service.list_tickets()
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "tickets": tickets,
            "priorities": list(Priority),
            "statuses": list(TicketStatus),
        },
    )


@router.post("/tickets")
def create_ticket_form(
    title: str = Form(...),
    description: str = Form(""),
    priority: Priority = Form(Priority.MEDIUM),
    assignee: str = Form(""),
    service: TicketService = Depends(get_ticket_service),
):
    ticket = service.create_ticket(title, description, priority, assignee or None)
    return RedirectResponse(url=f"/tickets/{ticket.id}", status_code=303)


@router.get("/tickets/{ticket_id}", response_class=HTMLResponse)
def ticket_detail(
    ticket_id: int,
    request: Request,
    service: TicketService = Depends(get_ticket_service),
):
    try:
        ticket = service.get_ticket(ticket_id)
    except TicketNotFound:
        return templates.TemplateResponse(
            request,
            "not_found.html",
            {"ticket_id": ticket_id},
            status_code=404,
        )
    return templates.TemplateResponse(
        request,
        "ticket_detail.html",
        {
            "ticket": ticket,
            "statuses": list(TicketStatus),
            "error": None,
        },
    )


@router.post("/tickets/{ticket_id}/status")
def change_status_form(
    ticket_id: int,
    request: Request,
    status: TicketStatus = Form(...),
    service: TicketService = Depends(get_ticket_service),
):
    try:
        service.change_status(ticket_id, status)
        return RedirectResponse(url=f"/tickets/{ticket_id}", status_code=303)
    except InvalidStatusTransition as exc:
        ticket = service.get_ticket(ticket_id)
        return templates.TemplateResponse(
            request,
            "ticket_detail.html",
            {"ticket": ticket, "statuses": list(TicketStatus), "error": str(exc)},
            status_code=409,
        )


@router.post("/tickets/{ticket_id}/comments")
def add_comment_form(
    ticket_id: int,
    request: Request,
    body: str = Form(...),
    author: str = Form(...),
    service: TicketService = Depends(get_ticket_service),
):
    try:
        service.add_comment(ticket_id, body, author)
        return RedirectResponse(url=f"/tickets/{ticket_id}", status_code=303)
    except TicketClosedError as exc:
        ticket = service.get_ticket(ticket_id)
        return templates.TemplateResponse(
            request,
            "ticket_detail.html",
            {"ticket": ticket, "statuses": list(TicketStatus), "error": str(exc)},
            status_code=409,
        )
