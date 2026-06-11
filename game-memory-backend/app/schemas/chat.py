from pydantic import BaseModel
from datetime import datetime
from typing import List


class ChatMessage(BaseModel):
    role: str   # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    user_game_id: int
    message: str


class ChatResponse(BaseModel):
    reply: str
    history: List[ChatMessage]


class ChatHistoryOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}
