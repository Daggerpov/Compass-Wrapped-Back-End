from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Literal
from datetime import datetime
from pydantic.json import timedelta_isoformat

class TransitEvent(BaseModel):
    """Model representing a transit event (tap in, tap out, or transfer)"""
    datetime: datetime
    transaction_type: str  # Tap in, Tap out, Transfer
    location: str
    journey_id: str

class TotalStats(BaseModel):
    """Model for total usage statistics"""
    total_taps: int
    total_journeys: int

class RouteStats(BaseModel):
    """Model for route statistics"""
    most_used_stops: List[Dict[str, Any]]
    most_used_stations: List[Dict[str, Any]]

class TimeStats(BaseModel):
    """Model for time-related statistics"""
    total_hours: float
    total_days: float
    average_trip_duration: float

class TransferStats(BaseModel):
    """Model for transfer statistics"""
    favorite_transfers: List[Dict[str, Any]]
    common_routes: List[Dict[str, Any]]

class PersonalityType(BaseModel):
    """Model for commuter personality type"""
    time_personality: str
    location_personality: str
    personality_description: str
    stats: Dict[str, Any]

class Achievements(BaseModel):
    """Model for achievements and milestones"""
    achievements: List[Dict[str, Any]]
    fun_stats: Dict[str, Any]

class MissingTaps(BaseModel):
    """Model for missing tap events"""
    missing_tap_ins: int
    missing_tap_outs: int
    details: Optional[List[Dict[str, Any]]]

class CompassWrappedStats(BaseModel):
    """Complete model for Compass Wrapped statistics"""
    total_stats: TotalStats
    route_stats: RouteStats
    time_stats: TimeStats
    transfer_stats: TransferStats
    personality: PersonalityType
    achievements: Achievements
    missing_taps: MissingTaps

class Stop(BaseModel):
    stop_name: str
    count: Optional[int] = None

class Route(BaseModel):
    route_name: str
    count: Optional[int] = None

class TimePeriod(BaseModel):
    start_date: str  # ISO format string
    end_date: str    # ISO format string
    period_type: Literal["weekly", "monthly", "yearly"]
    total_days: int

    def __init__(self, **data):
        super().__init__(**data)
        # Validate ISO format strings
        try:
            datetime.fromisoformat(self.start_date.replace('Z', '+00:00'))
            datetime.fromisoformat(self.end_date.replace('Z', '+00:00'))
        except ValueError as e:
            raise ValueError("Dates must be in ISO format") from e

class UserEstimate(BaseModel):
    estimated_trips_per_week: int
    actual_trips_per_week: float
    accuracy_percentage: float

class UserStats(BaseModel):
    user_id: str  # Anonymized user identifier
    total_trips: int
    total_hours: float
    most_used_transit: str  # e.g., "Bus", "SkyTrain", etc.
    top_stops: List[Stop]
    top_routes: List[Route]
    time_period: TimePeriod
    user_estimate: Optional[UserEstimate] = None
    created_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "anon_123",
                "total_trips": 245,
                "total_hours": 194.5,
                "most_used_transit": "SkyTrain",
                "top_stops": [
                    {"stop_name": "Broadway-City Hall Stn", "count": 76},
                    {"stop_name": "UBC Loop", "count": 52}
                ],
                "top_routes": [
                    {"route_name": "99 B-Line", "count": 120},
                    {"route_name": "Expo Line", "count": 80}
                ],
                "time_period": {
                    "start_date": "2023-01-01T00:00:00Z",
                    "end_date": "2023-12-31T23:59:59Z",
                    "period_type": "yearly",
                    "total_days": 365
                }
            }
        }

class ComparisonStats(BaseModel):
    percentile: float
    average_trips_per_week: float
    comparison_message: str

class TransitPersonality(BaseModel):
    type: str  # e.g., "Transit Veteran", "Casual Commuter", "Weekend Warrior"
    description: str
    percentile: float  # User's percentile among all users
    estimate_accuracy: Optional[str] = None

class UserStatsResponse(BaseModel):
    stats: UserStats
    personality: TransitPersonality
    comparison: ComparisonStats

    class Config:
        json_schema_extra = {
            "example": {
                "stats": {
                    "user_id": "anon_123",
                    "total_trips": 245,
                    "total_hours": 194.5,
                    "most_used_transit": "SkyTrain",
                    "top_stops": [
                        {"stop_name": "Broadway-City Hall Stn", "count": 76}
                    ],
                    "top_routes": [
                        {"route_name": "99 B-Line", "count": 120}
                    ],
                    "time_period": {
                        "start_date": "2023-01-01T00:00:00Z",
                        "end_date": "2023-12-31T23:59:59Z",
                        "period_type": "yearly",
                        "total_days": 365
                    }
                },
                "personality": {
                    "type": "Transit Veteran",
                    "description": "You're among the top transit users!",
                    "percentile": 95.5,
                    "estimate_accuracy": "Your estimate was spot on! You know your transit habits well."
                },
                "comparison": {
                    "percentile": 95.5,
                    "average_trips_per_week": 12.5,
                    "comparison_message": "You take 25% more trips than you estimated!"
                }
            }
        } 