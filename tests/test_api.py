from fastapi.testclient import TestClient

from app.models import TicketStatus


def test_health(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_and_get_ticket(client: TestClient) -> None:
    created = client.post(
        "/api/tickets",
        json={"title": "API ticket", "priority": "high"},
    )
    assert created.status_code == 201
    ticket_id = created.json()["id"]

    fetched = client.get(f"/api/tickets/{ticket_id}")
    assert fetched.status_code == 200
    assert fetched.json()["title"] == "API ticket"
    assert fetched.json()["priority"] == "high"


def test_invalid_status_transition_returns_409(client: TestClient) -> None:
    created = client.post("/api/tickets", json={"title": "Bad jump"})
    ticket_id = created.json()["id"]
    response = client.post(
        f"/api/tickets/{ticket_id}/status",
        json={"status": TicketStatus.CLOSED},
    )
    assert response.status_code == 409


def test_board_page_renders(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "Board" in response.text
