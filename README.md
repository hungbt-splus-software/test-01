# Desk

Dummy FastAPI fullstack (API + Jinja2) để sau này gắn tool sinh tài liệu spec và unit test.

Không dùng database. Store nằm trong memory, restart app là mất data.

## Chạy app

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

- UI: http://127.0.0.1:8000
- OpenAPI: http://127.0.0.1:8000/docs

## Test

```bash
pytest
```

## Domain dummy

Ticket board với vài rule cố ý để spec/UT có chỗ bám:

- Status: `open` → `in_progress` → `resolved` → `closed` (không được nhảy bước)
- Ticket `closed` không được update / delete / comment
- Filter list theo `status` và `priority`

## Cấu trúc

```
app/
  main.py                 FastAPI app
  models.py               Ticket, Comment, enums
  schemas.py              Pydantic request/response
  store.py                In-memory store
  services/ticket_service.py
  routers/api.py          REST
  routers/pages.py        HTML
tests/
```
