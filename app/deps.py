from fastapi import Depends

from app.services.label_service import LabelService
from app.services.member_service import MemberService
from app.services.project_service import ProjectService
from app.services.stats_service import StatsService
from app.services.ticket_service import TicketService
from app.services.worklog_service import WorklogService
from app.store import InMemoryStore

_store = InMemoryStore()


def get_store() -> InMemoryStore:
    return _store


def get_ticket_service(store: InMemoryStore = Depends(get_store)) -> TicketService:
    return TicketService(store)


def get_member_service(store: InMemoryStore = Depends(get_store)) -> MemberService:
    return MemberService(store)


def get_project_service(store: InMemoryStore = Depends(get_store)) -> ProjectService:
    return ProjectService(store)


def get_label_service(store: InMemoryStore = Depends(get_store)) -> LabelService:
    return LabelService(store)


def get_worklog_service(store: InMemoryStore = Depends(get_store)) -> WorklogService:
    return WorklogService(store)


def get_stats_service(store: InMemoryStore = Depends(get_store)) -> StatsService:
    return StatsService(store)
