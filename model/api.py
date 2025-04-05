from fastapi import FastAPI, HTTPException, Depends, Query
from pydantic import BaseModel
import json
import logging
from sqlalchemy.orm import Session
from session_manager import SessionManager, SessionLocal
from tutor_chain import TutorChain  # Your tutor chain implementation
from typing import List

logger = logging.getLogger(__name__)
app = FastAPI(title="AI Tutor API")

# Dependency to get the database session.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ChatRequest(BaseModel):
    session_id: int = None   # Resume session if provided.
    user_input: str
    username: str = None     # Optional: to link session to a user.

class ChatResponse(BaseModel):
    session_id: int
    response: str

class ConversationResponse(BaseModel):
    session_id: int
    user_message: str
    ai_response: str
    updated_at: str

# Initialize the tutor chain (singleton)
tutor_chain_instance = TutorChain()

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request_data: ChatRequest, db: Session = Depends(get_db)):
    sm = SessionManager(db)
    
    # Retrieve or create session.
    if request_data.session_id:
        session_obj = sm.get_session(request_data.session_id)
        print("sesssionnnn1!!!", session_obj.user_id)
        if not session_obj:
            raise HTTPException(status_code=404, detail="Session not found")
    else:
        # Create a user if username is provided.
        user_id = None
        if request_data.username:
            user = sm.get_user_by_username(request_data.username) or sm.create_user(request_data.username)
            user_id = user.id
        
        initial_state = {
            "user_profile": {"name": request_data.username, "interests": []},
            "current_course": "",
            "current_lesson": "",
            "completed_courses": [],
            "user_input": "",
            "multi_requests": [],
            "agent_responses": {},
            "agent_partial_responses": {},
            "conversational_response": "",
            "context_references": {},
            "should_exit": False,
            "history": []
        }
        session_obj = sm.create_session(user_id=user_id, initial_state=initial_state)
    
    # Load current state from session with all fields
    state = sm.get_session_state(session_obj)
    
    # Retrieve the conversation history
    if session_obj.user_id:
        history = sm.get_conversation_history(session_obj.id, session_obj.user_id, limit=10)
        # Inject history into state under a temporary key; it won't be persisted.
        # print("FSFSAFASDA" , history)
        state["db_history"] = history
        
        

    # Set the current user input.
    state["user_input"] = request_data.user_input

    try:
        # Invoke the tutor chain with the updated state.
        results = tutor_chain_instance.invoke(state)
        state.update(results)
        
        # Persist state changes with separate fields
        sm.update_session_state(session_obj, state)
        
        ai_response = state.get("conversational_response", "")
        if not ai_response:
            raise Exception("AI response is null. Rolling back transaction.")
        
        # Create a temporary user if none exists.
        user_id = session_obj.user_id
        if not user_id:
            temp_username = f"temp_user_{session_obj.id}"
            temp_user = sm.create_user(temp_username)
            user_id = temp_user.id
            session_obj.user_id = user_id
            db.flush()
        
        # Save the conversation separately.
        sm.add_to_conversation_history(session_obj, user_id, request_data.user_input, ai_response)
        sm.upsert_conversation(session_obj, user_id, request_data.user_input, ai_response)
        
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error("Transaction failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
    
    return ChatResponse(session_id=session_obj.id, response=ai_response)
class ConversationHistoryResponse(BaseModel):
    session_id: int
    messages: List[dict]

@app.get("/conversation/history", response_model=ConversationHistoryResponse)
def get_conversation_history(
    session_id: int = Query(..., description="The session ID"),
    user_id: int = Query(..., description="The user ID"),
    limit: int = Query(10, description="Maximum number of messages to retrieve"),
    db: Session = Depends(get_db)
):
    sm = SessionManager(db)
    session_obj = sm.get_session(session_id)
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")
    if session_obj.user_id != user_id:
        raise HTTPException(status_code=403, detail="User not authorized for this session")
    
    # Get conversation history filtering by both session and user
    history = sm.get_conversation_history(session_id, user_id, limit=limit)
    
    return ConversationHistoryResponse(
        session_id=session_id,
        messages=[{
            "user_message": entry["input"],
            "ai_response": entry["response"],
            "timestamp": entry.get("created_at")
        } for entry in history]
    )
