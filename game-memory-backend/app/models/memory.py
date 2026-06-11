from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, func
from sqlalchemy.orm import relationship
from app.db.session import Base


class Memory(Base):
    """
    A single game session memory.
    Created when user uploads screenshot + optional note,
    then AI analyzes and generates structured summary.
    """
    __tablename__ = "memories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    user_game_id = Column(Integer, ForeignKey("user_games.id", ondelete="CASCADE"), nullable=False, index=True)

    # User input
    user_note = Column(Text, nullable=True)          # optional text note from user
    screenshot_url = Column(String(500), nullable=True)  # uploaded screenshot path

    # AI-generated fields
    title = Column(String(300), nullable=True)          # e.g. "Defeated the Ice Dragon"
    summary = Column(Text, nullable=True)               # full narrative summary
    important_characters = Column(JSON, nullable=True)  # ["Captain Arlen", "Sara"]
    current_objective = Column(String(500), nullable=True)  # "Travel to Frost City"
    side_quests = Column(JSON, nullable=True)           # ["Help the blacksmith", ...]
    key_decisions = Column(JSON, nullable=True)         # important choices made
    location = Column(String(300), nullable=True)       # in-game location
    ai_raw_response = Column(Text, nullable=True)       # full raw AI response for debugging

    # Timeline
    session_date = Column(DateTime(timezone=True), nullable=True)   # when the session happened
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="memories")
    user_game = relationship("UserGame", back_populates="memories")

    def __repr__(self):
        return f"<Memory(id={self.id}, title={self.title})>"
