from pydantic import BaseModel
from typing import List

class ChatRequest(BaseModel):
    session_id: int = None
    user_input: str
    user_id: str = None
    username: str = None

class ChatResponse(BaseModel):
    session_id: int
    response: str

class ConversationResponse(BaseModel):
    session_id: int
    user_message: str
    ai_response: str
    updated_at: str
 
class ConversationHistoryResponse(BaseModel):
    session_id: int
    messages: List[dict]
 