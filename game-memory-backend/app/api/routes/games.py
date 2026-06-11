from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.game import AddGameToLibrary, UserGameOut, GameOut
from app.services.game_service import (
    get_or_create_game,
    get_game_by_id,
    search_games,
    add_game_to_library,
    get_user_games,
    get_user_game,
    remove_game_from_library,
)

router = APIRouter(prefix="/games", tags=["Games"])


@router.get("/search", response_model=List[GameOut])
async def search_game_catalog(
    q: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Search games in global catalog."""
    return await search_games(db, q)


@router.get("/library", response_model=List[UserGameOut])
async def get_my_games(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all games in the current user's library."""
    return await get_user_games(db, current_user.id)


@router.post("/library", response_model=UserGameOut, status_code=status.HTTP_201_CREATED)
async def add_game(
    data: AddGameToLibrary,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a game to user's library. Provide game_id OR game_name."""
    if data.game_id:
        game = await get_game_by_id(db, data.game_id)
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")
    elif data.game_name:
        game = await get_or_create_game(db, data.game_name)
    else:
        raise HTTPException(status_code=422, detail="Provide either game_id or game_name")

    user_game = await add_game_to_library(
        db,
        user_id=current_user.id,
        game_id=game.id,
        custom_name=data.custom_name,
        cover_image_url=data.cover_image_url,
    )
    return user_game


@router.get("/library/{user_game_id}", response_model=UserGameOut)
async def get_game_detail(
    user_game_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific game from user's library."""
    user_game = await get_user_game(db, user_game_id, current_user.id)
    if not user_game:
        raise HTTPException(status_code=404, detail="Game not in your library")
    return user_game


@router.delete("/library/{user_game_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_game(
    user_game_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a game from user's library."""
    deleted = await remove_game_from_library(db, user_game_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Game not in your library")
