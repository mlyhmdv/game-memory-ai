from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.models.chat import ChatHistory


async def save_message(
    db: AsyncSession,
    user_id: int,
    user_game_id: int,
    role: str,
    content: str,
) -> ChatHistory:
    msg = ChatHistory(
        user_id=user_id,
        user_game_id=user_game_id,
        role=role,
        content=content,
    )
    db.add(msg)
    await db.flush()
    return msg


async def get_chat_history(
    db: AsyncSession,
    user_id: int,
    user_game_id: int,
    limit: int = 50,
) -> List[ChatHistory]:
    result = await db.execute(
        select(ChatHistory)
        .where(
            ChatHistory.user_id == user_id,
            ChatHistory.user_game_id == user_game_id,
        )
        .order_by(ChatHistory.created_at.asc())
        .limit(limit)
    )
    return result.scalars().all()


async def clear_chat_history(db: AsyncSession, user_id: int, user_game_id: int):
    from sqlalchemy import delete
    await db.execute(
        delete(ChatHistory).where(
            ChatHistory.user_id == user_id,
            ChatHistory.user_game_id == user_game_id,
        )
    )
