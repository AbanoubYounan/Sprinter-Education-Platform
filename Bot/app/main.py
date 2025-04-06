from fastapi import FastAPI
from .endpoints import chat, conversation

app = FastAPI(title="AI Tutor API")

app.include_router(chat.router)
app.include_router(conversation.router)
