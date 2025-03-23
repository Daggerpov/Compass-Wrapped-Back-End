from fastapi import APIRouter, UploadFile, File, Query
from fastapi.responses import JSONResponse
import pandas as pd
from typing import Dict, Any
import traceback
import logging

from app.services.analytics_service import AnalyticsService

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
    responses={404: {"description": "Not found"}},
)

@router.post("/analyze/")
async def analyze_compass_data(
    file: UploadFile = File(...),
    estimated_trips_per_week: int = Query(None, description="User's estimated number of trips per week")
) -> dict:
    """
    Upload a Compass Card CSV file to get comprehensive statistics
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")
    
    # Initialize result object with metadata
    result = {
        "file_info": {
            "filename": file.filename,
            "processed": False
        },
        "status": {
            "success": True,
            "errors": {}
        }
    }
    
    try:
        # Read file once
        contents = await file.read()
        df = AnalyticsService().process_csv(contents)
        
        # Update file info
        result["file_info"].update({
            "processed": True,
            "rows": len(df),
            "columns": list(df.columns),
            "journeys": df['JourneyId'].nunique()
        })
        
        # Process each analysis component independently
        analysis_components = [
            ("total_stats", AnalyticsService().calculate_total_stats),
            ("route_stats", AnalyticsService().calculate_route_stats),
            ("time_stats", AnalyticsService().calculate_time_stats),
            ("transfer_stats", AnalyticsService().calculate_transfer_stats),
            ("personality", AnalyticsService().determine_personality),
            ("achievements", AnalyticsService().calculate_achievements),
            ("missing_taps", AnalyticsService().find_missing_taps)
        ]
        
        # Process each component and handle exceptions
        for component_name, analysis_function in analysis_components:
            try:
                result[component_name] = analysis_function(df)
            except Exception as e:
                result["status"]["success"] = False
                result["status"]["errors"][component_name] = str(e)
                result[component_name] = None
                # Log the error for debugging
                logging.error(f"Error in {component_name}: {str(e)}")
                logging.debug(traceback.format_exc())
        
        # Generate statistics
        return AnalyticsService().generate_compass_wrapped(df, estimated_trips_per_week)
    
    except Exception as e:
        # Handle critical errors in file processing
        result["status"]["success"] = False
        result["status"]["errors"]["file_processing"] = str(e)
        return JSONResponse(
            status_code=500,
            content=result
        ) 