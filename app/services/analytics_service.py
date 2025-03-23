import pandas as pd
import io
from datetime import datetime
from typing import Dict, List, Any, Tuple
import re

class AnalyticsService:
    def __init__(self):
        pass
    
    def process_csv(self, file_content: bytes) -> pd.DataFrame:
        """Process the CSV file and return a DataFrame"""
        df = pd.read_csv(io.StringIO(file_content.decode('utf-8')))
        # Clean and preprocess the data
        df['DateTime'] = pd.to_datetime(df['DateTime'], format='%b-%d-%Y %I:%M %p', errors='coerce')
        df['JourneyId'] = pd.to_datetime(df['JourneyId'], errors='coerce')
        
        # Extract location name from LocationDisplay (remove product info)
        df['Location'] = df['LocationDisplay'].apply(lambda x: x.split('\n')[0] if isinstance(x, str) else x)
        
        # Extract transaction type
        df['TransactionType'] = df['Transaction'].apply(
            lambda x: 'Tap in' if 'Tap in' in str(x) 
                    else ('Tap out' if 'Tap out' in str(x) 
                         else ('Transfer' if 'Transfer' in str(x) else 'Other'))
        )
        
        # Extract location type (Bus Stop or Station)
        df['LocationType'] = df['Location'].apply(
            lambda x: 'Bus Stop' if 'Bus Stop' in str(x) 
                    else ('Station' if 'Stn' in str(x) else 'Other')
        )
        
        # Extract specific location name and ID
        def extract_location_info(location_str):
            if pd.isna(location_str):
                return None, None
                
            # For bus stops
            bus_match = re.search(r'Bus Stop (\d+)', location_str)
            if bus_match:
                return f"Bus Stop {bus_match.group(1)}", bus_match.group(1)
                
            # For stations
            station_match = re.search(r'([\w\-]+) Stn', location_str)
            if station_match:
                return f"{station_match.group(1)} Station", station_match.group(1)
                
            return location_str, None
            
        df['LocationName'], df['LocationId'] = zip(*df['Location'].apply(extract_location_info))
        
        return df
    
    def calculate_total_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate total usage statistics"""
        total_taps = len(df)
        total_journeys = df['JourneyId'].nunique()
        
        return {
            "total_taps": total_taps,
            "total_journeys": total_journeys
        }
    
    def calculate_route_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate most traveled routes"""
        # Most used stops (tap in locations)
        tap_ins = df[df['TransactionType'] == 'Tap in']
        tap_in_counts = tap_ins['LocationName'].value_counts().reset_index()
        tap_in_counts.columns = ['location', 'count']
        most_used_stops = tap_in_counts.head(5).to_dict('records')
        
        # Most used stations
        stations = df[df['LocationType'] == 'Station']
        station_counts = stations['LocationName'].value_counts().reset_index()
        station_counts.columns = ['station', 'count']
        most_used_stations = station_counts.head(5).to_dict('records')
        
        return {
            "most_used_stops": most_used_stops,
            "most_used_stations": most_used_stations
        }
    
    def calculate_time_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate time-related statistics"""
        # Group by JourneyId
        journey_groups = df.groupby('JourneyId')
        
        total_time_minutes = 0
        valid_journeys = 0
        
        for journey_id, journey_df in journey_groups:
            # Find tap in and tap out for this journey
            tap_in = journey_df[journey_df['TransactionType'] == 'Tap in']
            tap_out = journey_df[journey_df['TransactionType'] == 'Tap out']
            
            if not tap_in.empty and not tap_out.empty:
                tap_in_time = tap_in['DateTime'].min()
                tap_out_time = tap_out['DateTime'].max()
                
                # Calculate duration
                duration = (tap_out_time - tap_in_time).total_seconds() / 60
                
                # Only count if journey makes sense (positive duration, not too long)
                if 0 < duration < 240:  # Less than 4 hours
                    total_time_minutes += duration
                    valid_journeys += 1
        
        # Calculate statistics
        total_hours = total_time_minutes / 60
        total_days = total_hours / 24
        avg_trip_duration = total_time_minutes / valid_journeys if valid_journeys > 0 else 0
        
        return {
            "total_hours": round(total_hours, 2),
            "total_days": round(total_days, 2),
            "average_trip_duration": round(avg_trip_duration, 2)
        }
    
    def calculate_transfer_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate transfer statistics"""
        # Find transfers
        transfers = df[df['TransactionType'] == 'Transfer']
        
        # Count transfers by location
        transfer_counts = transfers['LocationName'].value_counts().reset_index()
        transfer_counts.columns = ['location', 'count']
        favorite_transfers = transfer_counts.head(5).to_dict('records')
        
        # Find common journey patterns (tap in -> transfer -> tap out)
        journey_groups = df.groupby('JourneyId')
        routes = []
        
        for journey_id, journey_df in journey_groups:
            sorted_journey = journey_df.sort_values('DateTime')
            
            if len(sorted_journey) >= 2:
                # Get locations in order
                locations = sorted_journey['LocationName'].tolist()
                
                if len(locations) > 0:
                    route = ' → '.join(locations)
                    routes.append(route)
        
        # Count common routes
        route_counts = pd.Series(routes).value_counts().reset_index()
        route_counts.columns = ['route', 'count']
        common_routes = route_counts.head(5).to_dict('records')
        
        return {
            "favorite_transfers": favorite_transfers,
            "common_routes": common_routes
        }
    
    def determine_personality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Determine commuter personality type"""
        # Time-based personality
        tap_ins = df[df['TransactionType'] == 'Tap in']
        
        # Extract hour of day
        tap_ins['hour'] = tap_ins['DateTime'].dt.hour
        
        # Count trips by hour
        hour_counts = tap_ins['hour'].value_counts().to_dict()
        
        # Define time ranges
        morning_trips = sum(hour_counts.get(h, 0) for h in range(5, 12))  # 5 AM - noon
        afternoon_trips = sum(hour_counts.get(h, 0) for h in range(12, 17))  # noon - 5 PM
        evening_trips = sum(hour_counts.get(h, 0) for h in range(17, 22))  # 5 PM - 10 PM
        night_trips = sum(hour_counts.get(h, 0) for h in range(22, 24)) + sum(hour_counts.get(h, 0) for h in range(0, 5))
        
        total_trips = morning_trips + afternoon_trips + evening_trips + night_trips
        
        # Determine time personality
        time_personality = "Balanced Commuter"
        time_description = "You travel evenly throughout the day."
        
        if total_trips > 0:
            morning_pct = morning_trips / total_trips
            afternoon_pct = afternoon_trips / total_trips
            evening_pct = evening_trips / total_trips
            night_pct = night_trips / total_trips
            
            if morning_pct > 0.5:
                time_personality = "Early Bird"
                time_description = f"You're an Early Bird—{int(morning_pct*100)}% of your trips happen before noon!"
            elif afternoon_pct > 0.5:
                time_personality = "Daytime Rider"
                time_description = f"You're a Daytime Rider—{int(afternoon_pct*100)}% of your trips happen in the afternoon!"
            elif evening_pct > 0.5:
                time_personality = "Evening Explorer"
                time_description = f"You're an Evening Explorer—{int(evening_pct*100)}% of your trips happen in the evening!"
            elif night_pct > 0.3:
                time_personality = "Night Rider"
                time_description = f"You're a Night Rider—{int(night_pct*100)}% of your trips happen at night!"
        
        # Location-based personality
        location_counts = df['LocationName'].nunique()
        common_locations = df['LocationName'].value_counts()
        most_common_location_count = common_locations.max() if not common_locations.empty else 0
        most_common_location = common_locations.idxmax() if not common_locations.empty else "Unknown"
        
        # Determine location personality
        location_personality = "Regular Commuter"
        location_description = "You have a balanced mix of locations."
        
        unique_journeys = df['JourneyId'].nunique()
        
        if location_counts > 20 and unique_journeys > 30:
            location_personality = "City Explorer"
            location_description = f"You're a City Explorer with {location_counts} different locations visited!"
        elif most_common_location_count > 0.6 * df['JourneyId'].nunique():
            location_personality = "Vanilla Commuter"
            location_description = f"You're a Vanilla Commuter—you frequently visit {most_common_location}!"
        elif unique_journeys < 10:
            location_personality = "Sleeper"
            location_description = "There were many rides this year, and you were only part of a few—you're missing out!"
        
        # Combine personalities
        personality_description = f"{time_description} {location_description}"
        
        stats = {
            "morning_trips": morning_trips,
            "afternoon_trips": afternoon_trips,
            "evening_trips": evening_trips,
            "night_trips": night_trips,
            "unique_locations": location_counts,
            "most_common_location": most_common_location,
            "most_common_location_count": int(most_common_location_count)
        }
        
        return {
            "time_personality": time_personality,
            "location_personality": location_personality,
            "personality_description": personality_description,
            "stats": stats
        }
    
    def calculate_achievements(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate achievements and fun stats"""
        achievements = []
        total_trips = df['JourneyId'].nunique()
        
        # Trip milestones
        if total_trips >= 300:
            achievements.append({
                "name": "Transit Veteran",
                "description": f"You took {total_trips} trips this year!"
            })
        elif total_trips >= 100:
            achievements.append({
                "name": "Regular Commuter",
                "description": f"You took {total_trips} trips this year!"
            })
        elif total_trips >= 50:
            achievements.append({
                "name": "Transit Enthusiast",
                "description": f"You took {total_trips} trips this year!"
            })
        
        # Most used route
        routes = df['Transaction'].str.extract(r'(\d+)').dropna()
        if not routes.empty:
            route_counts = routes[0].value_counts()
            if not route_counts.empty:
                most_used_route = route_counts.index[0]
                route_count = route_counts.iloc[0]
                achievements.append({
                    "name": f"R{most_used_route} Warrior",
                    "description": f"You used the R{most_used_route} route {route_count} times!"
                })
        
        # Multi-transfer journeys
        journey_groups = df.groupby('JourneyId')
        multi_transfer_count = 0
        
        for journey_id, journey_df in journey_groups:
            transfers = journey_df[journey_df['TransactionType'] == 'Transfer']
            if len(transfers) >= 3:
                multi_transfer_count += 1
                
        if multi_transfer_count >= 3:
            achievements.append({
                "name": "Multi-Transfer Master",
                "description": f"You made {multi_transfer_count} journeys with 3+ transfers!"
            })
        
        # Fun stats
        earliest_trip = df['DateTime'].min() if not df.empty else None
        latest_trip = df['DateTime'].max() if not df.empty else None
        
        fun_stats = {
            "total_trips": total_trips,
            "earliest_trip": earliest_trip.strftime("%b %d, %Y at %I:%M %p") if earliest_trip is not None else None,
            "latest_trip": latest_trip.strftime("%b %d, %Y at %I:%M %p") if latest_trip is not None else None,
            "days_active": (latest_trip - earliest_trip).days + 1 if earliest_trip is not None and latest_trip is not None else 0
        }
        
        return {
            "achievements": achievements,
            "fun_stats": fun_stats
        }
        
    def find_missing_taps(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Find missing tap-ins and tap-outs"""
        journey_groups = df.groupby('JourneyId')
        
        missing_tap_ins = 0
        missing_tap_outs = 0
        missing_details = []
        
        for journey_id, journey_df in journey_groups:
            has_tap_in = any(journey_df['TransactionType'] == 'Tap in')
            has_tap_out = any(journey_df['TransactionType'] == 'Tap out')
            
            if not has_tap_in and not has_tap_out:
                # Skip journeys with neither tap in nor tap out (probably just transfers)
                continue
                
            if not has_tap_in:
                missing_tap_ins += 1
                first_event = journey_df.iloc[0]
                missing_details.append({
                    "journey_id": journey_id.strftime("%Y-%m-%d") if not pd.isna(journey_id) else "Unknown",
                    "missing_type": "Tap in",
                    "datetime": first_event['DateTime'].strftime("%b %d, %Y at %I:%M %p") if not pd.isna(first_event['DateTime']) else "Unknown",
                    "location": first_event['LocationName']
                })
            
            if not has_tap_out:
                missing_tap_outs += 1
                last_event = journey_df.iloc[-1]
                missing_details.append({
                    "journey_id": journey_id.strftime("%Y-%m-%d") if not pd.isna(journey_id) else "Unknown",
                    "missing_type": "Tap out",
                    "datetime": last_event['DateTime'].strftime("%b %d, %Y at %I:%M %p") if not pd.isna(last_event['DateTime']) else "Unknown",
                    "location": last_event['LocationName']
                })
        
        return {
            "missing_tap_ins": missing_tap_ins,
            "missing_tap_outs": missing_tap_outs,
            "details": missing_details[:10]  # Limit to 10 details
        }
    
    def generate_compass_wrapped(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate complete Compass Wrapped statistics"""
        # Calculate all statistics
        total_stats = self.calculate_total_stats(df)
        route_stats = self.calculate_route_stats(df)
        time_stats = self.calculate_time_stats(df)
        transfer_stats = self.calculate_transfer_stats(df)
        personality = self.determine_personality(df)
        achievements = self.calculate_achievements(df)
        missing_taps = self.find_missing_taps(df)
        
        # Combine all results
        return {
            "total_stats": total_stats,
            "route_stats": route_stats,
            "time_stats": time_stats,
            "transfer_stats": transfer_stats,
            "personality": personality,
            "achievements": achievements,
            "missing_taps": missing_taps
        } 