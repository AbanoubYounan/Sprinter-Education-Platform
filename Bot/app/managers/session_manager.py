import json
import uuid  # Add if not already imported
import logging
from datetime import datetime
from sqlalchemy import desc
from app.db.models import User, Conversation, ConversationHistory, Session, SessionFile
from sqlalchemy.orm import joinedload


# Create a module-level logger
logger = logging.getLogger(__name__)

class SessionManager:
    def __init__(self, db: Session):
        self.db = db
        self.logger = logger  # Make logger available to use in methods

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
        # Remove ephemeral data that shouldn't be persisted
        state_to_store = {key: value for key, value in state.items()
                          if key not in ["history", "db_history", "agent_responses",
                                         "agent_partial_responses", "conversational_response"]}

        # Update individual fields using the provided state
        if "current_course" in state_to_store:
            session_obj.current_course = state_to_store.get("current_course", "")

        if "current_lesson" in state_to_store:
            session_obj.current_lesson = state_to_store.get("current_lesson", "")

        # Update completed_courses as a JSON list
        if "completed_courses" in state_to_store:
            completed_courses = state_to_store.get("completed_courses", [])
            if session_obj.completed_courses:
                existing_courses = json.loads(session_obj.completed_courses)
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
                existing_interests = json.loads(session_obj.user_interests)
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
    
    def get_file_history(self, session_id: int, limit: int = 10):
        file_records = (
            self.db.query(SessionFile)
            .filter(SessionFile.session_id == session_id)
            .order_by(desc(SessionFile.created_at))
            .limit(limit)
            .all()
        )
        # Reverse the list to return history in chronological order (oldest first)
        result = []
        for file_entry in reversed(file_records):
            result.append({
                "original_filename": file_entry.original_filename,
                "file_path": file_entry.file_path,
                "summary": file_entry.summary,
                "extracted_content": file_entry.extracted_content,
                "tool_config": json.loads(file_entry.tool_config) if file_entry.tool_config else {},
                "created_at": file_entry.created_at.isoformat() if file_entry.created_at else None,
            })
        return result


    def get_session_state(self, session_obj: Session):
        state = {}
        state["current_course"] = session_obj.current_course or ""
        state["current_lesson"] = session_obj.current_lesson or ""
        state["completed_courses"] = (
            json.loads(session_obj.completed_courses) if session_obj.completed_courses else []
        )
        state["user_profile"] = {}
        state["user_profile"]["interests"] = (
            json.loads(session_obj.user_interests) if session_obj.user_interests else []
        )
        
        # Load conversation history and format it for the tutor chain.
        history = self.get_conversation_history(session_obj.id, session_obj.user_id, limit=5)
        conversation_history = []
        for entry in history:
            conversation_history.append({"role": "user", "content": entry["input"]})
            conversation_history.append({"role": "assistant", "content": entry["response"]})
        state["history"] = conversation_history

        # Load file history using the dedicated method.
        file_history = self.get_file_history(session_obj.id, limit=10)
        # print("HEREEE", file_history)
        
        # Convert file_history list to dictionary.
        files_dict = {}
        for file_info in file_history:
            # Use 'file_path' if available; fallback to 'original_filename' or generate a UUID.
            file_key = file_info.get("file_path") or file_info.get("original_filename") or str(uuid.uuid4())
            files_dict[file_key] = file_info
        state["files"] = files_dict

        return state

    def save_file(self, session_obj, file_info):
        """
        Save a file record (SessionFile) to the database associated with the given session.
        """
        session_file = SessionFile(
            session_id=session_obj.id,
            original_filename=file_info["original_filename"],
            file_path=file_info["file_path"],
            extracted_content=file_info["extracted_content"],
            summary=file_info["summary"],
            tool_config=json.dumps(file_info["tool_config"])  # Serialize configuration as JSON string.
        )

        self.db.add(session_file)
        self.db.commit()  # Commit so the file record is saved.
        self.db.refresh(session_file)  # Refresh if you need the file object’s ID later.

        self.logger.info("File processed and summary generated for: %s", file_info["original_filename"])
        return session_file

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
        """
        return self.db.query(User).filter(User.username == username).first()
