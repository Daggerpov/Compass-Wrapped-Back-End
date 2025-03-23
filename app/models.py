from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime

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