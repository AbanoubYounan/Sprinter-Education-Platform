from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.schemas import ChatRequest, ChatResponse
from app.dependencies import get_db
from app.managers.session_manager import SessionManager
from app.tutor_chain.core import TutorChain
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize the tutor chain (singleton)
tutor_chain_instance = TutorChain()

@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(request_data: ChatRequest, db: Session = Depends(get_db)):
    sm = SessionManager(db)
    
    # Retrieve or create session.
    if request_data.session_id:
        session_obj = sm.get_session(request_data.session_id)
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
        history = sm.get_conversation_history(session_obj.id, session_obj.user_id, limit=5)
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
