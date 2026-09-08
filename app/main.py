from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.routers.api import router as api_router
from app.routers.pages import router as pages_router

APP_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="Desk",
    description="Dummy FastAPI fullstack ticket board for spec and unit-test tooling.",
    version=__version__,
)
app.mount("/static", StaticFiles(directory=APP_DIR / "static"), name="static")
app.include_router(api_router, prefix="/api")
app.include_router(pages_router)
