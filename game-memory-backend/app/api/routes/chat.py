from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse, ChatHistoryOut, ChatMessage
from app.services.ai_service import chat_with_ai
from app.services.chat_service import (
    save_message,
    get_chat_history,
    clear_chat_history,
)
from app.services.memory_service import get_memories_for_game
from app.services.game_service import get_user_game

router = APIRouter(prefix="/chat", tags=["AI Chat"])


@router.post("/message", response_model=ChatResponse)
async def send_message(
    data: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Send a message to AI about a specific game.
    AI uses all the player's memories as context.
    """
    user_game = await get_user_game(db, data.user_game_id, current_user.id)
    if not user_game:
        raise HTTPException(status_code=404, detail="Game not in your library")

    # Fetch memories and chat history
    memories = await get_memories_for_game(db, data.user_game_id, current_user.id)
    history = await get_chat_history(db, current_user.id, data.user_game_id)
    game_name = user_game.custom_name or user_game.game.name

    # Save user message first
    await save_message(db, current_user.id, data.user_game_id, "user", data.message)

    # Get AI reply
    reply = await chat_with_ai(
        user_message=data.message,
        memories=memories,
        game_name=game_name,
        chat_history=history,
    )

    # Save AI reply
    await save_message(db, current_user.id, data.user_game_id, "assistant", reply)

    # Fetch updated history to return
    updated_history = await get_chat_history(db, current_user.id, data.user_game_id)

    return ChatResponse(
        reply=reply,
        history=[ChatMessage(role=m.role, content=m.content) for m in updated_history],
    )


@router.get("/history/{user_game_id}", response_model=List[ChatHistoryOut])
async def get_history(
    user_game_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get full chat history for a game."""
    user_game = await get_user_game(db, user_game_id, current_user.id)
    if not user_game:
        raise HTTPException(status_code=404, detail="Game not in your library")

    history = await get_chat_history(db, current_user.id, user_game_id)
    return [ChatHistoryOut.model_validate(m) for m in history]


@router.delete("/history/{user_game_id}", status_code=204)
async def clear_history(
    user_game_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Clear chat history for a game (start fresh)."""
    user_game = await get_user_game(db, user_game_id, current_user.id)
    if not user_game:
        raise HTTPException(status_code=404, detail="Game not in your library")

    await clear_chat_history(db, current_user.id, user_game_id)
