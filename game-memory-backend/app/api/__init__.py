from fastapi import APIRouter
from app.api.routes import auth, games, memories, chat

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(games.router)
api_router.include_router(memories.router)
api_router.include_router(chat.router)
