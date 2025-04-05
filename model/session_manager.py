# session_manager.py
import json
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint, desc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session

# Database configuration (SQLite example)
DATABASE_URL = "sqlite:///./app.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Existing Models ---

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    sessions = relationship("Session", back_populates="user")
# --- Conversation Models ---

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

# session_manager.py (updated Session model)
class Session(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Original JSON state for backward compatibility
    state_json = Column(Text, default="{}")
    
    # Individual state fields
    current_course = Column(String, nullable=True)
    current_lesson = Column(String, nullable=True)
    completed_courses = Column(Text, nullable=True)  # JSON list
    user_interests = Column(Text, nullable=True)     # JSON list
    last_intent = Column(String, nullable=True)
    last_tool = Column(String, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    conversation = relationship("Conversation", uselist=False, back_populates="session")

# Create all tables at startup
Base.metadata.create_all(bind=engine)

# --- SessionManager Class ---
class SessionManager:
    def __init__(self, db: Session):
        self.db = db

    def create_user(self, username: str):
        user = User(username=username)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_user(self, user_id: int):
        return self.db.query(User).filter(User.id == user_id).first()
        
    def get_user_by_username(self, username: str):
        """
        Get a user by username.
        
        Args:
            username: The username to search for
            
        Returns:
            User object if found, None otherwise
        """
        return self.db.query(User).filter(User.username == username).first()

    def create_session(self, user_id: int = None, initial_state: dict = None):
        if initial_state is None:
            initial_state = {}
            
        # Extract individual state fields
        current_course = initial_state.get("current_course", "")
        current_lesson = initial_state.get("current_lesson", "")
        completed_courses = json.dumps(initial_state.get("completed_courses", []))
        user_interests = json.dumps(initial_state.get("user_profile", {}).get("interests", []))
            
        session_obj = Session(
            user_id=user_id,
            state_json=json.dumps(initial_state),  # Keep for backward compatibility
            current_course=current_course,
            current_lesson=current_lesson,
            completed_courses=completed_courses,
            user_interests=user_interests
        )
        self.db.add(session_obj)
        self.db.commit()
        self.db.refresh(session_obj)
        return session_obj

    def update_session_state(self, session_obj: Session, state: dict):
        # Remove ephemeral data before persisting the state
        state_to_store = {key: value for key, value in state.items() 
                         if key not in ["history", "db_history", "agent_responses", 
                                        "agent_partial_responses", "conversational_response"]}
        
        # Update the JSON state for backward compatibility
        session_obj.state_json = json.dumps(state_to_store)
        
        # Update individual fields
        if "current_course" in state_to_store:
            session_obj.current_course = state_to_store.get("current_course", "")
            
        if "current_lesson" in state_to_store:
            session_obj.current_lesson = state_to_store.get("current_lesson", "")
        
        # Update completed_courses as a JSON list
        if "completed_courses" in state_to_store:
            completed_courses = state_to_store.get("completed_courses", [])
            if session_obj.completed_courses:
                # Merge with existing courses
                existing_courses = json.loads(session_obj.completed_courses)
                # Add new courses that aren't already in the list
                for course in completed_courses:
                    if course not in existing_courses:
                        existing_courses.append(course)
                session_obj.completed_courses = json.dumps(existing_courses)
            else:
                session_obj.completed_courses = json.dumps(completed_courses)
        
        # Update user interests
        if "user_profile" in state_to_store and "interests" in state_to_store["user_profile"]:
            new_interests = state_to_store["user_profile"]["interests"]
            if session_obj.user_interests:
                # Merge with existing interests
                existing_interests = json.loads(session_obj.user_interests)
                # Add new interests that aren't already in the list
                for interest in new_interests:
                    if interest not in existing_interests:
                        existing_interests.append(interest)
                session_obj.user_interests = json.dumps(existing_interests)
            else:
                session_obj.user_interests = json.dumps(new_interests)
        
        # Update last intent and tool if available
        if "current_interaction" in state_to_store:
            session_obj.last_intent = state_to_store["current_interaction"].get("intent", "")
            session_obj.last_tool = state_to_store["current_interaction"].get("tool", "")
            
        self.db.flush()

    def get_session(self, session_id: int):
        return self.db.query(Session).filter(Session.id == session_id).first()
    
    def get_session_state(self, session_obj: Session):
        try:
            state = json.loads(session_obj.state_json)
        except Exception:
            state = {}
            
        state["current_course"] = session_obj.current_course or ""
        state["current_lesson"] = session_obj.current_lesson or ""
        state["completed_courses"] = json.loads(session_obj.completed_courses) if session_obj.completed_courses else []
        
        if "user_profile" not in state:
            state["user_profile"] = {}
        state["user_profile"]["interests"] = json.loads(session_obj.user_interests) if session_obj.user_interests else []
        
        # Ensure the "history" key exists
        if "history" not in state:
            state["history"] = []
        
        return state

    
    def upsert_conversation(self, session_obj: Session, user_id: int, user_message: str, ai_response: str):
        # Look for an existing conversation for this session.
        conversation = self.db.query(Conversation).filter(Conversation.session_id == session_obj.id).first()
        if conversation:
            conversation.user_message = user_message
            conversation.ai_response = ai_response
        else:
            conversation = Conversation(
                session_id=session_obj.id,
                user_id=user_id,
                user_message=user_message,
                ai_response=ai_response
            )
            self.db.add(conversation)
        self.db.flush()
        return conversation

    def get_conversation(self, session_obj: Session):
        return self.db.query(Conversation).filter(Conversation.session_id == session_obj.id).first()

    def close(self):
        self.db.close()
            
    def get_conversation_history(self, session_id: int, user_id: int, limit: int = 10):
        history = self.db.query(ConversationHistory).filter(
            ConversationHistory.session_id == session_id,
            ConversationHistory.user_id == user_id
        ).order_by(desc(ConversationHistory.created_at)).limit(limit).all()
        
        # Reverse the list to return history in chronological order (oldest first)
        result = []
        for entry in reversed(history):
            result.append({
                "input": entry.user_message,
                "response": entry.ai_response,
                "created_at": entry.created_at.isoformat() if entry.created_at else None
            })
        return result

    def add_to_conversation_history(self, session_obj, user_id, user_message, ai_response):
        """
        Add a new entry to the conversation history.
        
        Args:
            session_obj: Session object
            user_id: User ID
            user_message: User's message
            ai_response: AI's response
        """
        history_entry = ConversationHistory(
            session_id=session_obj.id,
            user_id=user_id,
            user_message=user_message,
            ai_response=ai_response
        )
        self.db.add(history_entry)
        self.db.flush()
    def __init__(self, db: Session):
        self.db = db

    def create_user(self, username: str):
        user = User(username=username)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_user(self, user_id: int):
        return self.db.query(User).filter(User.id == user_id).first()

    def create_session(self, user_id: int = None, initial_state: dict = None):
        if initial_state is None:
            initial_state = {}
        session_obj = Session(
            user_id=user_id,
            state_json=json.dumps(initial_state),
            current_course=initial_state.get("current_course", ""),
            completed_courses=json.dumps(initial_state.get("completed_courses", []))
        )
        self.db.add(session_obj)
        self.db.commit()
        self.db.refresh(session_obj)
        return session_obj

    def update_session_state(self, session_obj: Session, state: dict):
        # Remove chat conversation data before persisting the state.
        state_to_store = {key: value for key, value in state.items() if key != "history"}
        session_obj.state_json = json.dumps(state_to_store)
        session_obj.current_course = state_to_store.get("current_course", "")
        session_obj.completed_courses = json.dumps(state_to_store.get("completed_courses", []))
        self.db.flush()

    def get_session(self, session_id: int):
        return self.db.query(Session).filter(Session.id == session_id).first()
    
    def upsert_conversation(self, session_obj: Session, user_id: int, user_message: str, ai_response: str):
        # Look for an existing conversation for this session.
        conversation = self.db.query(Conversation).filter(Conversation.session_id == session_obj.id).first()
        if conversation:
            conversation.user_message = user_message
            conversation.ai_response = ai_response
        else:
            conversation = Conversation(
                session_id=session_obj.id,
                user_id=user_id,
                user_message=user_message,
                ai_response=ai_response
            )
            self.db.add(conversation)
        self.db.flush()
        return conversation

    def get_conversation(self, session_obj: Session):
        return self.db.query(Conversation).filter(Conversation.session_id == session_obj.id).first()

    def close(self):
        self.db.close()
            
    def get_conversation_history(self, session_id: int, user_id: int, limit: int = 10):
        history = self.db.query(ConversationHistory).filter(
            ConversationHistory.session_id == session_id,
            ConversationHistory.user_id == user_id
        ).order_by(desc(ConversationHistory.created_at)).limit(limit).all()
        
        # Reverse the list to return history in chronological order (oldest first)
        result = []
        for entry in reversed(history):
            result.append({
                "input": entry.user_message,
                "response": entry.ai_response,
                "created_at": entry.created_at.isoformat() if entry.created_at else None
            })
        return result


    def add_to_conversation_history(self, session_obj, user_id, user_message, ai_response):
        """
        Add a new entry to the conversation history.
        
        Args:
            session_obj: Session object
            user_id: User ID
            user_message: User's message
            ai_response: AI's response
        """
        history_entry = ConversationHistory(
            session_id=session_obj.id,
            user_id=user_id,
            user_message=user_message,
            ai_response=ai_response
        )
        self.db.add(history_entry)
        self.db.flush()
        
    def get_user_by_username(self, username: str):
        """
        Get a user by username.
        
        Args:
            username: The username to search for
            
        Returns:
            User object if found, None otherwise
        """
        return self.db.query(User).filter(User.username == username).first()
