from fastapi import APIRouter

from app.routers import api, labels, members, pages, projects, stats

api_router = APIRouter()
api_router.include_router(api.router)
api_router.include_router(members.router)
api_router.include_router(projects.router)
api_router.include_router(labels.router)
api_router.include_router(stats.router)

pages_router = pages.router
