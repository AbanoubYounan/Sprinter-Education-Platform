import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint, desc
from sqlalchemy.orm import relationship
from app.db.database import Base, engine


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    sessions = relationship("Session", back_populates="user")


class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False, unique=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user_message = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    session = relationship("Session", back_populates="conversation")
    user = relationship("User")
    
    # Ensures one conversation per session
    __table_args__ = (
        UniqueConstraint('session_id', name='uq_session_conversation'),
    )

class ConversationHistory(Base):
    __tablename__ = "conversation_history"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user_message = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    session = relationship("Session")
    user = relationship("User")

# Updated Session model
class Session(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Original JSON state for backward compatibility
    # state_json = Column(Text, default="{}")
    
    # Individual state fields
    current_course = Column(String, nullable=True)
    current_lesson = Column(String, nullable=True)
    completed_courses = Column(Text, nullable=True)
    user_interests = Column(Text, nullable=True)
    last_intent = Column(String, nullable=True)
    last_tool = Column(String, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    conversation = relationship("Conversation", uselist=False, back_populates="session")
    
class SessionFile(Base):
    __tablename__ = "session_files"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    summary = Column(Text, nullable=True)
    extracted_content = Column(Text, nullable=True)
    tool_config = Column(Text, nullable=True)  # Serialized JSON
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # This allows you to access the session via session_obj.files
    session = relationship("Session", backref="files")
# Create all tables at startup
Base.metadata.create_all(bind=engine)
