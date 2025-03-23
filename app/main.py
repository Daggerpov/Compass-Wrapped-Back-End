from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
from .routers import stats
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Compass Wrapped API",
    description="API for analyzing Compass Card data and generating year in review statistics",
    version="1.0.0"
)

# CORS configuration
origins = [
    "http://localhost:5173",  # Vite dev server
    "http://localhost:3000",  # Alternative local development
    "https://compass-wrapped.vercel.app",  # Production frontend
    "https://compass-wrapped-front-end.vercel.app"  # Alternative production domain
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

# Include routers
app.include_router(stats.router)

@app.get("/")
async def root():
    try:
        # Ping MongoDB
        await app.mongodb_client.admin.command('ping')
        mongo_status = "Connected"
    except Exception as e:
        mongo_status = f"Error: {str(e)}"
    
    return {
        "message": "Welcome to Compass Wrapped API",
        "docs": "/docs",
        "version": "1.0.0",
        "mongodb_status": mongo_status
    } 