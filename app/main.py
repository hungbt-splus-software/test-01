from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.routers.api import router as ticket_router
from app.routers.labels import router as labels_router
from app.routers.members import router as members_router
from app.routers.pages import router as pages_router
from app.routers.projects import router as projects_router
from app.routers.stats import router as stats_router

APP_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="Desk",
    description="Dummy FastAPI fullstack ticket board for spec and unit-test tooling.",
    version=__version__,
)
app.mount("/static", StaticFiles(directory=APP_DIR / "static"), name="static")
app.include_router(ticket_router, prefix="/api")
app.include_router(members_router, prefix="/api")
app.include_router(projects_router, prefix="/api")
app.include_router(labels_router, prefix="/api")
app.include_router(stats_router, prefix="/api")
app.include_router(pages_router)
