from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import relationship
from app.db.session import Base


class Game(Base):
    """Global game catalog"""
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, nullable=False, index=True)
    genre = Column(String(100), nullable=True)
    cover_image_url = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user_games = relationship("UserGame", back_populates="game")

    def __repr__(self):
        return f"<Game(id={self.id}, name={self.name})>"


class UserGame(Base):
    """User's game library — links users to games they play"""
    __tablename__ = "user_games"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    game_id = Column(Integer, ForeignKey("games.id", ondelete="CASCADE"), nullable=False)
    custom_name = Column(String(200), nullable=True)   # override game name
    cover_image_url = Column(String(500), nullable=True)  # custom cover
    total_sessions = Column(Integer, default=0)
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    last_played_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="games")
    game = relationship("Game", back_populates="user_games")
    memories = relationship("Memory", back_populates="user_game", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<UserGame(user_id={self.user_id}, game_id={self.game_id})>"
