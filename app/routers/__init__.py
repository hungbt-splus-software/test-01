from fastapi import APIRouter

from app.routers import api, pages

api_router = APIRouter()
api_router.include_router(api.router)

pages_router = pages.router
