from datetime import datetime
from typing import List, Optional
from ..models import UserStats, TransitPersonality, UserStatsResponse
import numpy as np
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

class UserStatsService:
    def __init__(self, db_client: AsyncIOMotorClient):
        self.db = db_client.compass_wrapped
        self.stats_collection = self.db.user_stats

    async def save_user_stats(self, stats: UserStats) -> str:
        stats_dict = stats.dict()
        stats_dict['created_at'] = datetime.now()
        result = await self.stats_collection.insert_one(stats_dict)
        return str(result.inserted_id)

    async def get_user_stats(self, user_id: str) -> Optional[UserStats]:
        stats = await self.stats_collection.find_one({"user_id": user_id})
        if stats:
            return UserStats(**stats)
        return None

    async def calculate_percentiles(self, total_trips: int, total_hours: float) -> dict:
        # Get all stats for comparison
        all_stats = await self.stats_collection.find().to_list(length=None)
        
        if not all_stats:
            return {"trips_percentile": 50, "hours_percentile": 50}

        all_trips = [stat['total_trips'] for stat in all_stats]
        all_hours = [stat['total_hours'] for stat in all_stats]

        trips_percentile = np.percentile(all_trips, total_trips)
        hours_percentile = np.percentile(all_hours, total_hours)

        return {
            "trips_percentile": float(trips_percentile),
            "hours_percentile": float(hours_percentile)
        }

    def determine_personality(self, trips_percentile: float) -> TransitPersonality:
        if trips_percentile >= 90:
            return TransitPersonality(
                type="Transit Veteran",
                description="You're a true transit champion! Your dedication to public transportation is remarkable.",
                percentile=trips_percentile
            )
        elif trips_percentile >= 70:
            return TransitPersonality(
                type="Frequent Rider",
                description="You're a seasoned transit user who knows their way around the system.",
                percentile=trips_percentile
            )
        elif trips_percentile >= 40:
            return TransitPersonality(
                type="Regular Commuter",
                description="You're a reliable transit user making good use of the system.",
                percentile=trips_percentile
            )
        elif trips_percentile >= 20:
            return TransitPersonality(
                type="Casual Rider",
                description="You use transit occasionally and are building your experience.",
                percentile=trips_percentile
            )
        else:
            return TransitPersonality(
                type="Transit Explorer",
                description="You're just getting started with your transit journey!",
                percentile=trips_percentile
            )

    async def process_user_stats(self, stats: UserStats) -> UserStatsResponse:
        # Save stats
        await self.save_user_stats(stats)

        # Calculate percentiles
        percentiles = await self.calculate_percentiles(stats.total_trips, stats.total_hours)

        # Determine personality
        personality = self.determine_personality(percentiles["trips_percentile"])

        return UserStatsResponse(
            stats=stats,
            personality=personality,
            ranking=percentiles
        ) 