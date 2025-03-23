from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
from .routers import stats
from dotenv import load_dotenv
import logging
import traceback
from fastapi.responses import JSONResponse

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Compass Wrapped API",
    description="API for analyzing Compass Card data and generating year in review statistics",
    version="1.0.0"
)

# CORS configuration - more permissive for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins during development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# MongoDB connection
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")

@app.on_event("startup")
async def startup_db_client():
    app.mongodb_client = AsyncIOMotorClient(MONGODB_URL)
    app.mongodb = app.mongodb_client.compass_wrapped

@app.on_event("shutdown")
async def shutdown_db_client():
    app.mongodb_client.close()

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception handler caught: {exc}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={
            "message": "Internal server error",
            "detail": str(exc),
            "type": type(exc).__name__
        }
    )

# Include routers
app.include_router(stats.router)

@app.get("/")
async def root():
    try:
        # Ping MongoDB
        await app.mongodb_client.admin.command('ping')
        mongo_status = "Connected"
    except Exception as e:
        logger.error(f"MongoDB connection error: {e}")
        mongo_status = f"Error: {str(e)}"
    
    return {
        "message": "Welcome to Compass Wrapped API",
        "docs": "/docs",
        "version": "1.0.0",
        "mongodb_status": mongo_status
    } 