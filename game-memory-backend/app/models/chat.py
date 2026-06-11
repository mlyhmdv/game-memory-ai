from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import relationship
from app.db.session import Base


class ChatHistory(Base):
    """
    Stores Q&A chat between user and AI about their game memories.
    Used for "Continue Journey" feature.
    """
    __tablename__ = "chat_histories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    user_game_id = Column(Integer, ForeignKey("user_games.id", ondelete="CASCADE"), nullable=False, index=True)

    role = Column(String(20), nullable=False)   # "user" or "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="chat_histories")

    def __repr__(self):
        return f"<ChatHistory(id={self.id}, role={self.role})>"
