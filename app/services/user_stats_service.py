from datetime import datetime
from typing import List, Optional
from ..models import UserStats, TransitPersonality, UserStatsResponse, ComparisonStats
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

    async def calculate_comparison_stats(self, stats: UserStats) -> ComparisonStats:
        # Get all stats for the same period type
        all_stats = await self.stats_collection.find({
            "time_period.period_type": stats.time_period.period_type
        }).to_list(length=None)
        
        if not all_stats:
            return ComparisonStats(
                percentile=50,
                average_trips_per_week=stats.total_trips / (stats.time_period.total_days / 7),
                comparison_message="Not enough data for comparison yet"
            )

        # Calculate trips per week for comparison
        current_trips_per_week = stats.total_trips / (stats.time_period.total_days / 7)
        all_trips_per_week = [
            s['total_trips'] / (s['time_period']['total_days'] / 7) 
            for s in all_stats
        ]

        percentile = float(np.percentile(all_trips_per_week, current_trips_per_week))
        
        # Generate comparison message
        comparison_message = self._generate_comparison_message(
            stats.user_estimate.estimated_trips_per_week if stats.user_estimate else None,
            current_trips_per_week
        )

        return ComparisonStats(
            percentile=percentile,
            average_trips_per_week=current_trips_per_week,
            comparison_message=comparison_message
        )

    def _generate_comparison_message(self, estimated: Optional[int], actual: float) -> str:
        if not estimated:
            return f"You take {actual:.1f} trips per week on average"
        
        difference_percent = ((actual - estimated) / estimated) * 100
        if abs(difference_percent) < 10:
            return "Your estimate was spot on!"
        elif difference_percent > 0:
            return f"You take {abs(difference_percent):.0f}% more trips than you estimated!"
        else:
            return f"You take {abs(difference_percent):.0f}% fewer trips than you estimated!"

    def determine_personality(self, percentile: float, estimate_accuracy: float = None) -> TransitPersonality:
        personality_type = ""
        description = ""
        estimate_message = None

        if percentile >= 90:
            personality_type = "Transit Veteran"
            description = "You're a true transit champion! Your dedication to public transportation is remarkable."
        elif percentile >= 70:
            personality_type = "Frequent Rider"
            description = "You're a seasoned transit user who knows their way around the system."
        elif percentile >= 40:
            personality_type = "Regular Commuter"
            description = "You're a reliable transit user making good use of the system."
        elif percentile >= 20:
            personality_type = "Casual Rider"
            description = "You use transit occasionally and are building your experience."
        else:
            personality_type = "Transit Explorer"
            description = "You're just getting started with your transit journey!"

        if estimate_accuracy is not None:
            if estimate_accuracy >= 90:
                estimate_message = "You know your transit habits incredibly well!"
            elif estimate_accuracy >= 70:
                estimate_message = "You have a good sense of your transit usage."
            else:
                estimate_message = "Your actual usage is quite different from what you expected!"

        return TransitPersonality(
            type=personality_type,
            description=description,
            percentile=percentile,
            estimate_accuracy=estimate_message
        )

    async def process_user_stats(self, stats: UserStats) -> UserStatsResponse:
        # Save stats
        await self.save_user_stats(stats)

        # Calculate comparison stats
        comparison = await self.calculate_comparison_stats(stats)

        # Calculate estimate accuracy if available
        estimate_accuracy = None
        if stats.user_estimate:
            estimate_accuracy = 100 - min(100, abs(
                ((stats.user_estimate.actual_trips_per_week - stats.user_estimate.estimated_trips_per_week) 
                 / stats.user_estimate.estimated_trips_per_week) * 100
            ))

        # Determine personality
        personality = self.determine_personality(
            comparison.percentile,
            estimate_accuracy
        )

        return UserStatsResponse(
            stats=stats,
            personality=personality,
            comparison=comparison
        ) 