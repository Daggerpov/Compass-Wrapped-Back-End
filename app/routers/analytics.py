from fastapi import APIRouter, UploadFile, File, HTTPException
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

analytics_service = AnalyticsService()

@router.post("/analyze/")
async def analyze_compass_data(file: UploadFile = File(...)):
    """
    Process a Compass Card CSV file and return all analytics data at once.
    Each analysis component is processed independently, so if one fails, the others will still be returned.
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
        df = analytics_service.process_csv(contents)
        
        # Update file info
        result["file_info"].update({
            "processed": True,
            "rows": len(df),
            "columns": list(df.columns),
            "journeys": df['JourneyId'].nunique()
        })
        
        # Process each analysis component independently
        analysis_components = [
            ("total_stats", analytics_service.calculate_total_stats),
            ("route_stats", analytics_service.calculate_route_stats),
            ("time_stats", analytics_service.calculate_time_stats),
            ("transfer_stats", analytics_service.calculate_transfer_stats),
            ("personality", analytics_service.determine_personality),
            ("achievements", analytics_service.calculate_achievements),
            ("missing_taps", analytics_service.find_missing_taps)
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
        
        return result
    
    except Exception as e:
        # Handle critical errors in file processing
        result["status"]["success"] = False
        result["status"]["errors"]["file_processing"] = str(e)
        return JSONResponse(
            status_code=500,
            content=result
        ) 