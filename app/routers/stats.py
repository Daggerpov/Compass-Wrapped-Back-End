from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from ..models import UserStats, UserStatsResponse
from ..services.user_stats_service import UserStatsService
from motor.motor_asyncio import AsyncIOMotorClient
from ..dependencies import get_db

router = APIRouter(
    prefix="/stats",
    tags=["stats"],
    responses={404: {"description": "Not found"}},
)

@router.post("/user", response_model=UserStatsResponse)
async def save_user_stats(
    stats: UserStats,
    db: AsyncIOMotorClient = Depends(get_db)
) -> UserStatsResponse:
    """
    Save user statistics and get their transit personality and rankings
    """
    stats_service = UserStatsService(db)
    return await stats_service.process_user_stats(stats)

@router.get("/user/{user_id}", response_model=Optional[UserStatsResponse])
async def get_user_stats(
    user_id: str,
    db: AsyncIOMotorClient = Depends(get_db)
) -> Optional[UserStatsResponse]:
    """
    Get user statistics by user ID
    """
    stats_service = UserStatsService(db)
    stats = await stats_service.get_user_stats(user_id)
    if not stats:
        raise HTTPException(status_code=404, detail="User stats not found")
    
    return await stats_service.process_user_stats(stats) 