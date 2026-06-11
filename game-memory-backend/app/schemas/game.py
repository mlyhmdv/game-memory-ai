from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class GameCreate(BaseModel):
    name: str
    genre: Optional[str] = None
    cover_image_url: Optional[str] = None
    description: Optional[str] = None


class GameOut(BaseModel):
    id: int
    name: str
    genre: Optional[str] = None
    cover_image_url: Optional[str] = None
    description: Optional[str] = None

    model_config = {"from_attributes": True}


class AddGameToLibrary(BaseModel):
    game_id: Optional[int] = None      # existing game from catalog
    game_name: Optional[str] = None    # or add by name (auto-creates game)
    custom_name: Optional[str] = None
    cover_image_url: Optional[str] = None


class UserGameOut(BaseModel):
    id: int
    user_id: int
    game_id: int
    game: GameOut
    custom_name: Optional[str] = None
    cover_image_url: Optional[str] = None
    total_sessions: int
    added_at: datetime
    last_played_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
