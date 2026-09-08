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

## Domain dummy (rule để spec/UT bám)

Tickets

- Status: `open` → `in_progress` → `resolved` → `closed` (không nhảy bước)
- Ticket `closed` không update / delete / comment / assign / label / worklog
- Filter theo `status`, `priority`, `project_id`, `q`, `overdue`
- Assignee phải là member `active`
- Không gắn ticket vào project đã archive

SLA (`app/sla.py`)

- high = 8h, medium = 24h, low = 72h (tính từ `created_at`)
- Đổi priority thì tính lại `due_at`
- `resolved` / `closed` không tính overdue

Members

- Username: `a-z0-9` và `-`, unique
- Không deactivate nếu còn ticket `open` / `in_progress`

Projects

- Slug unique, tự slugify từ name nếu bỏ trống
- Không archive nếu còn ticket chưa `closed`

Labels / worklogs

- Tối đa 3 label / ticket, không gắn trùng
- Worklog: `0 < hours <= 12`, tổng <= 40h / ticket

## Cấu trúc

```
app/
  sla.py text.py constants.py
  models.py schemas.py store.py
  services/     ticket, member, project, label, worklog, stats
  routers/      api, members, projects, labels, stats, pages
tests/          mẫu cũ, domain mới chưa viết test
```
