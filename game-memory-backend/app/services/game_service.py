from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Optional, List
from datetime import datetime

from app.models.game import Game, UserGame


async def get_or_create_game(db: AsyncSession, name: str) -> Game:
    result = await db.execute(select(Game).where(Game.name == name))
    game = result.scalar_one_or_none()
    if not game:
        game = Game(name=name)
        db.add(game)
        await db.flush()
        await db.refresh(game)
    return game


async def get_game_by_id(db: AsyncSession, game_id: int) -> Optional[Game]:
    result = await db.execute(select(Game).where(Game.id == game_id))
    return result.scalar_one_or_none()


async def search_games(db: AsyncSession, query: str) -> List[Game]:
    result = await db.execute(
        select(Game).where(Game.name.ilike(f"%{query}%")).limit(10)
    )
    return result.scalars().all()


async def add_game_to_library(
    db: AsyncSession,
    user_id: int,
    game_id: int,
    custom_name: Optional[str] = None,
    cover_image_url: Optional[str] = None,
) -> UserGame:
    # Check if already added
    result = await db.execute(
        select(UserGame).where(
            UserGame.user_id == user_id,
            UserGame.game_id == game_id,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    user_game = UserGame(
        user_id=user_id,
        game_id=game_id,
        custom_name=custom_name,
        cover_image_url=cover_image_url,
    )
    db.add(user_game)
    await db.flush()

    result = await db.execute(
        select(UserGame)
        .options(selectinload(UserGame.game))
        .where(UserGame.id == user_game.id)
    )
    return result.scalar_one()


async def get_user_games(db: AsyncSession, user_id: int) -> List[UserGame]:
    result = await db.execute(
        select(UserGame)
        .options(selectinload(UserGame.game))
        .where(UserGame.user_id == user_id)
        .order_by(UserGame.last_played_at.desc().nullslast(), UserGame.added_at.desc())
    )
    return result.scalars().all()


async def get_user_game(db: AsyncSession, user_game_id: int, user_id: int) -> Optional[UserGame]:
    result = await db.execute(
        select(UserGame)
        .options(selectinload(UserGame.game))
        .where(UserGame.id == user_game_id, UserGame.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def update_last_played(db: AsyncSession, user_game_id: int):
    result = await db.execute(select(UserGame).where(UserGame.id == user_game_id))
    user_game = result.scalar_one_or_none()
    if user_game:
        user_game.last_played_at = datetime.utcnow()
        user_game.total_sessions += 1
        await db.flush()


async def remove_game_from_library(db: AsyncSession, user_game_id: int, user_id: int) -> bool:
    result = await db.execute(
        select(UserGame).where(UserGame.id == user_game_id, UserGame.user_id == user_id)
    )
    user_game = result.scalar_one_or_none()
    if not user_game:
        return False
    await db.delete(user_game)
    return True
