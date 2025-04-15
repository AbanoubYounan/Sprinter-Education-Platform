from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from app.models.schemas import ConversationHistoryResponse
from app.dependencies import get_db
from app.managers.session_manager import SessionManager

router = APIRouter()

@router.get("/conversation/history", response_model=ConversationHistoryResponse)
def get_conversation_history(
    session_id: int = Query(..., description="The session ID"),
    user_id: str = Query(..., description="The user ID"),
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
