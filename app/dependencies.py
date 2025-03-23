from fastapi import Request
from motor.motor_asyncio import AsyncIOMotorClient

def get_db(request: Request) -> AsyncIOMotorClient:
    return request.app.mongodb_client 