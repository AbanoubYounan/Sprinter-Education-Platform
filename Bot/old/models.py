from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    session_id: Optional[int] = None  # If provided, resume session; otherwise, create a new one
    user_input: str

class ChatResponse(BaseModel):
    session_id: int
    response: str
