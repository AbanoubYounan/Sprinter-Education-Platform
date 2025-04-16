import os
import uuid
import logging
import json  # For serializing tool_config
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.models.schemas import ChatRequest, ChatResponse
from app.dependencies import get_db
from app.managers.session_manager import SessionManager
from app.tutor_chain.core import TutorChain
from app.managers.pdf_manager import PDFSearchTool
# Import the new file model (if needed in other contexts)
from app.db.models import SessionFile

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize the tutor chain (singleton)
tutor_chain_instance = TutorChain()

def generate_file_summary(tutor, file_info) -> str:
    prompt = f"""
    You are an expert summarizer.
    
    Based on the details provided:
    - File Name: {file_info.get("original_filename", "")}
    - Extracted Content (sample): {file_info.get("extracted_content", "")[:1000]}
    - Tool Configuration: {file_info.get("tool_config", {})}
    
    Provide a concise, clear summary of the file content that captures its key points.
    """
    response = tutor.log_and_invoke(
        [{"role": "user", "content": prompt}],
        tool_name="file_summary_response"
    )
    logger.debug("Received response from tutor.log_and_invoke: %s", response)
    if isinstance(response, list):
        if response:
            # If each element is a dictionary with a "content" key, use key access.
            if isinstance(response[0], dict) and "content" in response[0]:
                return response[0]["content"]
            # Alternatively, if elements are objects with a 'content' attribute.
            elif hasattr(response[0], "content"):
                return response[0].content
        raise ValueError("Unexpected response format from tutor.log_and_invoke.")
    # If response is a dictionary, access directly.
    if isinstance(response, dict) and "content" in response:
        return response["content"]
    elif hasattr(response, "content"):
        return response.content
    else:
        raise ValueError("Response from tutor.log_and_invoke does not have a 'content' attribute.")



@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(
    request_data: str = Form(...),
    db: Session = Depends(get_db),
    uploaded_file: UploadFile = File(None)
):
    try:
        # Parse the JSON string into a ChatRequest model.
        chat_request = ChatRequest.model_validate_json(request_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON for ChatRequest: {e}")

    sm = SessionManager(db)
     
    # 1. Retrieve or create the session.
    session_obj = None
    if chat_request.session_id:
        session_obj = sm.get_session(chat_request.session_id)
        if not session_obj:
            raise HTTPException(status_code=404, detail="Session not found")
    else:
        user_id = None
        if hasattr(chat_request, "user_id") and chat_request.user_id:
            user_id = chat_request.user_id
        elif chat_request.username:
            user = sm.get_user_by_username(chat_request.username) or sm.create_user(chat_request.username)
            user_id = user.id
        
        initial_state = {
            "user_profile": {"name": chat_request.username, "interests": []},
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
            "history": [],
            "files": {},
            "course_names": tutor_chain_instance.course_names
        }
        session_obj = sm.create_session(user_id=user_id, initial_state=initial_state)
    
    state = sm.get_session_state(session_obj)
    
    # 2. Retrieve conversation history, if available.
    if session_obj.user_id:
        history = sm.get_conversation_history(session_obj.id, session_obj.user_id, limit=5)
        # print("history" , history)
        state["db_history"] = history
        
    # 3. Set current user input.
    state["user_input"] = chat_request.user_input

    # 4. File processing: store the uploaded file and generate a summary.
    if uploaded_file:
        try:
            file_ext = os.path.splitext(uploaded_file.filename)[-1]
            unique_filename = f"{uuid.uuid4()}{file_ext}"
            file_path = os.path.join("uploads", unique_filename)
            
            os.makedirs("uploads", exist_ok=True)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.file.read()) 
            
            pdf_tool_config = {
                "llm": {
                    "provider": "groq",
                    "config": {
                        "model": "groq/llama3-8b-8192",
                        "temperature": 0.5,
                        "top_p": 1,
                    }
                },
                "embedder": {
                    "provider": "google",
                    "config": {
                        "model": "models/embedding-001",
                        "task_type": "retrieval_document",
                    }
                },
            }
            
            file_info = {
                "original_filename": uploaded_file.filename,
                "file_path": file_path,
                "tool_config": pdf_tool_config
            }
            
            pdf_tool = PDFSearchTool(config=pdf_tool_config)
            extracted_content = pdf_tool.process(file_path)
            file_info["extracted_content"] = extracted_content

            # Generate a refined summary using the tutor chain.
            refined_summary = generate_file_summary(tutor_chain_instance, file_info)
            file_info["summary"] = refined_summary
            
            # Optionally, store the file metadata in the in-memory state.
            # print("REfined", file_info)
            files = state.get("files")
            if not isinstance(files, dict):
                # Log or handle the inconsistency before setting it to an empty dict.
                logger.warning("Expected state['files'] to be a dict but got %s. Reinitializing.", type(files))
                files = {}
                state["files"] = files
            files[unique_filename] = file_info
            
            # Use the SessionManager's method to save the file data to the DB.
            sm.save_file(session_obj, file_info)
            
        except Exception as e:
            logger.error("File processing error: %s", e)
            db.rollback()
            raise HTTPException(status_code=500, detail="File processing error")
    
    # 5. Process the conversation via the tutor chain.
    try:
        results = tutor_chain_instance.invoke(state) 
        
        state.update(results)
        
        sm.update_session_state(session_obj, state)
        
        ai_response = state.get("conversational_response", "")
        if not ai_response:
            raise Exception("AI response is null. Rolling back transaction.")
        
        if not session_obj.user_id:
            temp_username = f"temp_user_{session_obj.id}"
            temp_user = sm.create_user(temp_username)
            session_obj.user_id = temp_user.id
            db.flush()
        
        sm.add_to_conversation_history(session_obj, session_obj.user_id, chat_request.user_input, ai_response)
        sm.upsert_conversation(session_obj, session_obj.user_id, chat_request.user_input, ai_response)
        
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error("Transaction failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
    
    return ChatResponse(session_id=session_obj.id, response=ai_response)
