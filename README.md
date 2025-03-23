# Compass Wrapped Backend

A FastAPI backend for analyzing Compass Card transit data and generating statistics similar to Spotify Wrapped.

## Features

- Upload Compass Card CSV data
- Analyze transit patterns
- Calculate total usage statistics
- Identify most traveled routes
- Calculate total time spent on transit
- Identify favorite transfers
- Determine commuter personality type
- Earn achievements based on transit behavior
- Identify missing tap-ins/tap-outs

## Setup Instructions

1. Clone the repository
2. Create a virtual environment (recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Run the application:
   ```
   uvicorn app.main:app --reload
   ```
   or
   ```
   python run.py
   ```

5. Access the API documentation at:
   ```
   http://localhost:8000/docs
   ```

## API Endpoint

The API has been simplified to a single endpoint that returns all analytics data at once:

- `POST /analytics/analyze/`: Upload a CSV file and receive complete analysis

### Response Structure

The response includes all analytics, with each component processed independently:

```json
{
  "file_info": {
    "filename": "compass_data.csv",
    "processed": true,
    "rows": 100,
    "columns": ["DateTime", "Transaction", ...],
    "journeys": 25
  },
  "status": {
    "success": true,
    "errors": {}
  },
  "total_stats": {
    "total_taps": 100,
    "total_journeys": 25
  },
  "route_stats": {
    "most_used_stops": [...],
    "most_used_stations": [...]
  },
  "time_stats": {
    "total_hours": 15.5,
    "total_days": 0.65,
    "average_trip_duration": 37.2
  },
  "transfer_stats": {
    "favorite_transfers": [...],
    "common_routes": [...]
  },
  "personality": {
    "time_personality": "Early Bird",
    "location_personality": "City Explorer",
    "personality_description": "You're an Early Bird—65% of your trips happen before noon!",
    "stats": {...}
  },
  "achievements": {
    "achievements": [...],
    "fun_stats": {...}
  },
  "missing_taps": {
    "missing_tap_ins": 3,
    "missing_tap_outs": 2,
    "details": [...]
  }
}
```

If an individual component fails, it will return null for that component while still returning data for the others:

```json
{
  "file_info": {...},
  "status": {
    "success": false,
    "errors": {
      "time_stats": "Error calculating time statistics: ..."
    }
  },
  "total_stats": {...},
  "route_stats": {...},
  "time_stats": null,
  ...
}
```

## CSV Format

The application expects CSV data in the following format:

```
DateTime,Transaction,Product,LineItem,Amount,BalanceDetails,JourneyId,LocationDisplay,TransactonTime,OrderDate,Payment,OrderNumber,AuthCode,Total
Dec-21-2024 12:17 PM,Transfer at Bus Stop 61281,3 Zone UPass (N),,$0.00,$0.00,2024-12-21T20:03:00.0000000Z,"Transfer at Bus Stop 61281
3 Zone UPass (N)",12:17 PM,,,,,
...
```

## Example Usage

Using curl:

```bash
curl -X 'POST' \
  'http://localhost:8000/analytics/analyze/' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@compass_data.csv'
```
 
