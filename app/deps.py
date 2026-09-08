from fastapi import Depends

from app.services.ticket_service import TicketService
from app.store import InMemoryStore

_store = InMemoryStore()


def get_store() -> InMemoryStore:
    return _store


def get_ticket_service(store: InMemoryStore = Depends(get_store)) -> TicketService:
    return TicketService(store)
