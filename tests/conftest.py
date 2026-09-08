import pytest
from fastapi.testclient import TestClient

from app.deps import get_store, get_ticket_service
from app.main import app
from app.services.ticket_service import TicketService
from app.store import InMemoryStore


@pytest.fixture
def store() -> InMemoryStore:
    return InMemoryStore()


@pytest.fixture
def service(store: InMemoryStore) -> TicketService:
    return TicketService(store)


@pytest.fixture
def client(store: InMemoryStore) -> TestClient:
    app.dependency_overrides[get_store] = lambda: store
    app.dependency_overrides[get_ticket_service] = lambda: TicketService(store)
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
