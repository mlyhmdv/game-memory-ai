from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List

from app.models.memory import Memory


async def create_memory(db: AsyncSession, **kwargs) -> Memory:
    memory = Memory(**kwargs)
    db.add(memory)
    await db.flush()
    await db.refresh(memory)
    return memory


async def get_memory_by_id(db: AsyncSession, memory_id: int, user_id: int) -> Optional[Memory]:
    result = await db.execute(
        select(Memory).where(Memory.id == memory_id, Memory.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def get_memories_for_game(
    db: AsyncSession,
    user_game_id: int,
    user_id: int,
    limit: int = 100,
) -> List[Memory]:
    """Return all memories for a specific user+game, sorted by date (newest first)."""
    result = await db.execute(
        select(Memory)
        .where(Memory.user_game_id == user_game_id, Memory.user_id == user_id)
        .order_by(Memory.session_date.desc().nullslast(), Memory.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


async def get_last_memory(db: AsyncSession, user_game_id: int, user_id: int) -> Optional[Memory]:
    result = await db.execute(
        select(Memory)
        .where(Memory.user_game_id == user_game_id, Memory.user_id == user_id)
        .order_by(Memory.session_date.desc().nullslast(), Memory.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def delete_memory(db: AsyncSession, memory_id: int, user_id: int) -> bool:
    result = await db.execute(
        select(Memory).where(Memory.id == memory_id, Memory.user_id == user_id)
    )
    memory = result.scalar_one_or_none()
    if not memory:
        return False
    await db.delete(memory)
    return True


async def get_all_user_memories(db: AsyncSession, user_id: int) -> List[Memory]:
    """All memories across all games — for global search etc."""
    result = await db.execute(
        select(Memory)
        .where(Memory.user_id == user_id)
        .order_by(Memory.created_at.desc())
    )
    return result.scalars().all()
