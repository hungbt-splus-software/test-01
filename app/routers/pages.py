from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.deps import (
    get_label_service,
    get_member_service,
    get_project_service,
    get_stats_service,
    get_ticket_service,
    get_worklog_service,
)
from app.exceptions import DeskError, TicketNotFound
from app.models import Priority, TicketStatus
from app.services.label_service import LabelService
from app.services.member_service import MemberService
from app.services.project_service import ProjectService
from app.services.stats_service import StatsService
from app.services.ticket_service import TicketService
from app.services.worklog_service import WorklogService
from app.sla import hours_logged, is_overdue

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))
templates.env.globals["is_overdue"] = is_overdue
templates.env.globals["hours_logged"] = hours_logged


def _board_context(
    tickets,
    members,
    projects,
    error: str | None = None,
):
    return {
        "tickets": tickets,
        "members": members,
        "projects": [project for project in projects if not project.archived],
        "priorities": list(Priority),
        "statuses": list(TicketStatus),
        "error": error,
    }


@router.get("/", response_class=HTMLResponse)
def board(
    request: Request,
    q: str | None = None,
    tickets: TicketService = Depends(get_ticket_service),
    members: MemberService = Depends(get_member_service),
    projects: ProjectService = Depends(get_project_service),
):
    return templates.TemplateResponse(
        request,
        "index.html",
        _board_context(
            tickets.list_tickets(q=q),
            members.list_members(active=True),
            projects.list_projects(),
        )
        | {"q": q or ""},
    )


@router.post("/tickets")
def create_ticket_form(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    priority: Priority = Form(Priority.MEDIUM),
    assignee: str = Form(""),
    project_id: str = Form(""),
    tickets: TicketService = Depends(get_ticket_service),
    members: MemberService = Depends(get_member_service),
    projects: ProjectService = Depends(get_project_service),
):
    parsed_project = int(project_id) if project_id else None
    try:
        ticket = tickets.create_ticket(
            title,
            description,
            priority,
            assignee or None,
            parsed_project,
        )
        return RedirectResponse(url=f"/tickets/{ticket.id}", status_code=303)
    except DeskError as exc:
        return templates.TemplateResponse(
            request,
            "index.html",
            _board_context(
                tickets.list_tickets(),
                members.list_members(active=True),
                projects.list_projects(),
                str(exc),
            )
            | {"q": ""},
            status_code=400,
        )


@router.get("/tickets/{ticket_id}", response_class=HTMLResponse)
def ticket_detail(
    ticket_id: int,
    request: Request,
    tickets: TicketService = Depends(get_ticket_service),
    members: MemberService = Depends(get_member_service),
    projects: ProjectService = Depends(get_project_service),
    labels: LabelService = Depends(get_label_service),
):
    try:
        ticket = tickets.get_ticket(ticket_id)
    except TicketNotFound:
        return templates.TemplateResponse(
            request,
            "not_found.html",
            {"resource": "ticket", "item_id": ticket_id},
            status_code=404,
        )
    label_map = {label.id: label for label in labels.list_labels()}
    return templates.TemplateResponse(
        request,
        "ticket_detail.html",
        {
            "ticket": ticket,
            "statuses": list(TicketStatus),
            "members": members.list_members(active=True),
            "projects": [project for project in projects.list_projects() if not project.archived],
            "labels": labels.list_labels(),
            "ticket_labels": [label_map[label_id] for label_id in ticket.label_ids if label_id in label_map],
            "error": None,
        },
    )


@router.post("/tickets/{ticket_id}/status")
def change_status_form(
    ticket_id: int,
    request: Request,
    status: TicketStatus = Form(...),
    tickets: TicketService = Depends(get_ticket_service),
    members: MemberService = Depends(get_member_service),
    projects: ProjectService = Depends(get_project_service),
    labels: LabelService = Depends(get_label_service),
):
    try:
        tickets.change_status(ticket_id, status)
        return RedirectResponse(url=f"/tickets/{ticket_id}", status_code=303)
    except DeskError as exc:
        return _ticket_error(request, ticket_id, str(exc), tickets, members, projects, labels)


@router.post("/tickets/{ticket_id}/comments")
def add_comment_form(
    ticket_id: int,
    request: Request,
    body: str = Form(...),
    author: str = Form(...),
    tickets: TicketService = Depends(get_ticket_service),
    members: MemberService = Depends(get_member_service),
    projects: ProjectService = Depends(get_project_service),
    labels: LabelService = Depends(get_label_service),
):
    try:
        tickets.add_comment(ticket_id, body, author)
        return RedirectResponse(url=f"/tickets/{ticket_id}", status_code=303)
    except DeskError as exc:
        return _ticket_error(request, ticket_id, str(exc), tickets, members, projects, labels)


@router.post("/tickets/{ticket_id}/assign")
def assign_form(
    ticket_id: int,
    request: Request,
    username: str = Form(""),
    tickets: TicketService = Depends(get_ticket_service),
    members: MemberService = Depends(get_member_service),
    projects: ProjectService = Depends(get_project_service),
    labels: LabelService = Depends(get_label_service),
):
    try:
        tickets.assign(ticket_id, username or None)
        return RedirectResponse(url=f"/tickets/{ticket_id}", status_code=303)
    except DeskError as exc:
        return _ticket_error(request, ticket_id, str(exc), tickets, members, projects, labels)


@router.post("/tickets/{ticket_id}/project")
def set_project_form(
    ticket_id: int,
    request: Request,
    project_id: str = Form(""),
    tickets: TicketService = Depends(get_ticket_service),
    members: MemberService = Depends(get_member_service),
    projects: ProjectService = Depends(get_project_service),
    labels: LabelService = Depends(get_label_service),
):
    try:
        tickets.set_project(ticket_id, int(project_id) if project_id else None)
        return RedirectResponse(url=f"/tickets/{ticket_id}", status_code=303)
    except DeskError as exc:
        return _ticket_error(request, ticket_id, str(exc), tickets, members, projects, labels)


@router.post("/tickets/{ticket_id}/labels")
def attach_label_form(
    ticket_id: int,
    request: Request,
    label_id: int = Form(...),
    labels: LabelService = Depends(get_label_service),
    tickets: TicketService = Depends(get_ticket_service),
    members: MemberService = Depends(get_member_service),
    projects: ProjectService = Depends(get_project_service),
):
    try:
        labels.attach(ticket_id, label_id)
        return RedirectResponse(url=f"/tickets/{ticket_id}", status_code=303)
    except DeskError as exc:
        return _ticket_error(request, ticket_id, str(exc), tickets, members, projects, labels)


@router.post("/tickets/{ticket_id}/worklogs")
def add_worklog_form(
    ticket_id: int,
    request: Request,
    hours: float = Form(...),
    author: str = Form(...),
    note: str = Form(""),
    worklogs: WorklogService = Depends(get_worklog_service),
    tickets: TicketService = Depends(get_ticket_service),
    members: MemberService = Depends(get_member_service),
    projects: ProjectService = Depends(get_project_service),
    labels: LabelService = Depends(get_label_service),
):
    try:
        worklogs.add_worklog(ticket_id, hours, author, note)
        return RedirectResponse(url=f"/tickets/{ticket_id}", status_code=303)
    except DeskError as exc:
        return _ticket_error(request, ticket_id, str(exc), tickets, members, projects, labels)


@router.get("/members", response_class=HTMLResponse)
def members_page(
    request: Request,
    members: MemberService = Depends(get_member_service),
):
    return templates.TemplateResponse(
        request,
        "members.html",
        {"members": members.list_members(), "error": None},
    )


@router.post("/members")
def create_member_form(
    request: Request,
    username: str = Form(...),
    display_name: str = Form(...),
    members: MemberService = Depends(get_member_service),
):
    try:
        members.create_member(username, display_name)
        return RedirectResponse(url="/members", status_code=303)
    except DeskError as exc:
        return templates.TemplateResponse(
            request,
            "members.html",
            {"members": members.list_members(), "error": str(exc)},
            status_code=400,
        )


@router.post("/members/{member_id}/deactivate")
def deactivate_member_form(
    member_id: int,
    request: Request,
    members: MemberService = Depends(get_member_service),
):
    try:
        members.deactivate(member_id)
        return RedirectResponse(url="/members", status_code=303)
    except DeskError as exc:
        return templates.TemplateResponse(
            request,
            "members.html",
            {"members": members.list_members(), "error": str(exc)},
            status_code=409,
        )


@router.get("/projects", response_class=HTMLResponse)
def projects_page(
    request: Request,
    projects: ProjectService = Depends(get_project_service),
    tickets: TicketService = Depends(get_ticket_service),
):
    return templates.TemplateResponse(
        request,
        "projects.html",
        {
            "projects": projects.list_projects(),
            "tickets": tickets.list_tickets(),
            "error": None,
        },
    )


@router.post("/projects")
def create_project_form(
    request: Request,
    name: str = Form(...),
    slug: str = Form(""),
    projects: ProjectService = Depends(get_project_service),
    tickets: TicketService = Depends(get_ticket_service),
):
    try:
        projects.create_project(name, slug or None)
        return RedirectResponse(url="/projects", status_code=303)
    except DeskError as exc:
        return templates.TemplateResponse(
            request,
            "projects.html",
            {
                "projects": projects.list_projects(),
                "tickets": tickets.list_tickets(),
                "error": str(exc),
            },
            status_code=400,
        )


@router.post("/projects/{project_id}/archive")
def archive_project_form(
    project_id: int,
    request: Request,
    projects: ProjectService = Depends(get_project_service),
    tickets: TicketService = Depends(get_ticket_service),
):
    try:
        projects.archive(project_id)
        return RedirectResponse(url="/projects", status_code=303)
    except DeskError as exc:
        return templates.TemplateResponse(
            request,
            "projects.html",
            {
                "projects": projects.list_projects(),
                "tickets": tickets.list_tickets(),
                "error": str(exc),
            },
            status_code=409,
        )


@router.get("/stats", response_class=HTMLResponse)
def stats_page(
    request: Request,
    stats: StatsService = Depends(get_stats_service),
):
    return templates.TemplateResponse(request, "stats.html", {"stats": stats.summarize()})


def _ticket_error(
    request: Request,
    ticket_id: int,
    error: str,
    tickets: TicketService,
    members: MemberService,
    projects: ProjectService,
    labels: LabelService,
):
    ticket = tickets.get_ticket(ticket_id)
    label_map = {label.id: label for label in labels.list_labels()}
    return templates.TemplateResponse(
        request,
        "ticket_detail.html",
        {
            "ticket": ticket,
            "statuses": list(TicketStatus),
            "members": members.list_members(active=True),
            "projects": [project for project in projects.list_projects() if not project.archived],
            "labels": labels.list_labels(),
            "ticket_labels": [label_map[label_id] for label_id in ticket.label_ids if label_id in label_map],
            "error": error,
        },
        status_code=409,
    )
