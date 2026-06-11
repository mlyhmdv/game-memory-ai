import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.memory import LastSessionSummary, MemoryListItem, MemoryOut
from app.services.ai_service import (
    analyze_screenshot_and_note,
    generate_continue_journey_summary,
)
from app.services.game_service import get_user_game, update_last_played
from app.services.memory_service import (
    create_memory,
    delete_memory,
    get_last_memory,
    get_memories_for_game,
    get_memory_by_id,
)

router = APIRouter(prefix="/memories", tags=["Memories"])

UPLOAD_DIR = Path(settings.UPLOAD_DIR)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_SIZE = settings.MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


def _save_upload(file: UploadFile, user_id: int) -> str:
    """Save uploaded file, return relative path."""
    ext = Path(file.filename).suffix.lower() if file.filename else ".jpg"
    filename = f"user_{user_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}{ext}"
    dest = UPLOAD_DIR / filename
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return str(dest)


@router.post("/upload", response_model=MemoryOut, status_code=status.HTTP_201_CREATED)
async def upload_memory(
    user_game_id: int = Form(...),
    user_note: Optional[str] = Form(None),
    session_date: Optional[str] = Form(None),
    screenshot: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a screenshot and/or note for a game session.
    AI will analyze and generate a structured memory.
    """
    # Validate user_game belongs to current user
    user_game = await get_user_game(db, user_game_id, current_user.id)
    if not user_game:
        raise HTTPException(status_code=404, detail="Game not in your library")

    # Validate + save screenshot
    screenshot_path = None
    if screenshot and screenshot.filename:
        if screenshot.content_type not in ALLOWED_TYPES:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_TYPES)}",
            )
        # Check size
        contents = await screenshot.read()
        if len(contents) > MAX_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Max {settings.MAX_FILE_SIZE_MB}MB",
            )
        await screenshot.seek(0)
        screenshot_path = _save_upload(screenshot, current_user.id)

    if not screenshot_path and not user_note:
        raise HTTPException(
            status_code=422, detail="Provide either a screenshot or a note"
        )

    # Parse session date
    parsed_date = None
    if session_date:
        try:
            parsed_date = datetime.fromisoformat(session_date)
        except ValueError:
            parsed_date = datetime.utcnow()

    # Call AI
    game_name = user_game.custom_name or user_game.game.name
    ai_result = await analyze_screenshot_and_note(
        screenshot_path=screenshot_path,
        user_note=user_note,
        game_name=game_name,
    )

    # Save memory to DB
    memory = await create_memory(
        db,
        user_id=current_user.id,
        user_game_id=user_game_id,
        user_note=user_note,
        screenshot_url=screenshot_path,
        title=ai_result.get("title"),
        summary=ai_result.get("summary"),
        important_characters=ai_result.get("important_characters"),
        current_objective=ai_result.get("current_objective"),
        side_quests=ai_result.get("side_quests"),
        key_decisions=ai_result.get("key_decisions"),
        location=ai_result.get("location"),
        ai_raw_response=ai_result.get("ai_raw_response"),
        session_date=parsed_date or datetime.utcnow(),
    )

    # Update game stats
    await update_last_played(db, user_game_id)

    return MemoryOut.model_validate(memory)


@router.get("/game/{user_game_id}", response_model=List[MemoryListItem])
async def get_game_timeline(
    user_game_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all memories for a game — used for timeline view."""
    user_game = await get_user_game(db, user_game_id, current_user.id)
    if not user_game:
        raise HTTPException(status_code=404, detail="Game not in your library")

    memories = await get_memories_for_game(db, user_game_id, current_user.id)
    return [MemoryListItem.model_validate(m) for m in memories]


@router.get("/game/{user_game_id}/full", response_model=List[MemoryOut])
async def get_game_memories_full(
    user_game_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get full memory details for a game."""
    user_game = await get_user_game(db, user_game_id, current_user.id)
    if not user_game:
        raise HTTPException(status_code=404, detail="Game not in your library")

    memories = await get_memories_for_game(db, user_game_id, current_user.id)
    return [MemoryOut.model_validate(m) for m in memories]


@router.get("/game/{user_game_id}/continue", response_model=LastSessionSummary)
async def continue_journey(
    user_game_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    'Continue Journey' — AI generates a narrative summary of the last session
    and what the player should do next.
    """
    user_game = await get_user_game(db, user_game_id, current_user.id)
    if not user_game:
        raise HTTPException(status_code=404, detail="Game not in your library")

    memories = await get_memories_for_game(db, user_game_id, current_user.id, limit=10)
    last_memory = memories[0] if memories else None
    game_name = user_game.custom_name or user_game.game.name

    ai_summary = await generate_continue_journey_summary(memories, game_name)

    return LastSessionSummary(
        game_name=game_name,
        last_played=user_game.last_played_at,
        ai_summary=ai_summary,
        last_memory=MemoryOut.model_validate(last_memory) if last_memory else None,
        total_sessions=user_game.total_sessions,
    )


@router.get("/{memory_id}", response_model=MemoryOut)
async def get_memory(
    memory_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single memory by ID."""
    memory = await get_memory_by_id(db, memory_id, current_user.id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    return MemoryOut.model_validate(memory)


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory_route(
    memory_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a memory."""
    deleted = await delete_memory(db, memory_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory not found")
