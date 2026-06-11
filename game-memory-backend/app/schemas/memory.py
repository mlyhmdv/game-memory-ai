from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class MemoryCreate(BaseModel):
    user_game_id: int
    user_note: Optional[str] = None
    session_date: Optional[datetime] = None


class MemoryOut(BaseModel):
    id: int
    user_id: int
    user_game_id: int
    user_note: Optional[str] = None
    screenshot_url: Optional[str] = None

    # AI generated
    title: Optional[str] = None
    summary: Optional[str] = None
    important_characters: Optional[List[str]] = None
    current_objective: Optional[str] = None
    side_quests: Optional[List[str]] = None
    key_decisions: Optional[List[str]] = None
    location: Optional[str] = None

    session_date: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class MemoryListItem(BaseModel):
    """Compact memory for timeline view"""
    id: int
    title: Optional[str] = None
    location: Optional[str] = None
    screenshot_url: Optional[str] = None
    session_date: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class LastSessionSummary(BaseModel):
    """Returned by 'Continue Journey' endpoint"""
    game_name: str
    last_played: Optional[datetime]
    ai_summary: str                          # Full narrative from AI
    last_memory: Optional[MemoryOut] = None
    total_sessions: int
