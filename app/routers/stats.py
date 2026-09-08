from fastapi import APIRouter, Depends

from app.deps import get_stats_service
from app.schemas import BoardStatsOut
from app.services.stats_service import StatsService

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("", response_model=BoardStatsOut)
def board_stats(service: StatsService = Depends(get_stats_service)) -> BoardStatsOut:
    return service.summarize()
