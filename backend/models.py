from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    touches = relationship("Touch", back_populates="user")
    feedbacks = relationship("CharacteristicFeedback", back_populates="user")


class Touch(Base):
    __tablename__ = "touches"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    method_file_path = Column(String, nullable=True)
    n_bells = Column(Integer, nullable=True)
    rounds_rows = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user = relationship("User", back_populates="touches")
    performances = relationship("Performance", back_populates="touch", cascade="all, delete-orphan")


class Performance(Base):
    __tablename__ = "performances"
    id = Column(Integer, primary_key=True, index=True)
    touch_id = Column(Integer, ForeignKey("touches.id"), nullable=False)
    label = Column(String, nullable=False)
    timing_file_path = Column(String, nullable=True)
    order_index = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    touch = relationship("Touch", back_populates="performances")


class CharacteristicFeedback(Base):
    __tablename__ = "characteristic_feedbacks"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    characteristic_name = Column(String, nullable=False)
    is_useful = Column(Boolean, nullable=False)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user = relationship("User", back_populates="feedbacks")
