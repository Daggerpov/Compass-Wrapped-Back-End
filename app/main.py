from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io

# Import your router here
from app.routers import analytics

app = FastAPI(
    title="Compass Wrapped API",
    description="API for analyzing Compass Card transit data and generating comprehensive statistics",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(analytics.router)

@app.get("/")
async def root():
    return {
        "message": "Welcome to Compass Wrapped API",
        "endpoints": {
            "analyze": "/analytics/analyze/ - Upload a CSV file to get all statistics at once"
        }
    } 