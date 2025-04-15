import re
import json
from app.tutor_chain.config import logger

import re
import json
from app.tutor_chain.config import logger
from crewai_tools import PDFSearchTool
import os

def generate_search_query(tutor, state, additional_info="") -> str:
    # Reconstruct conversation history by pairing messages by role.
    history = state.get('history', [])
    chat_history = ""
    # Iterate over the history in pairs. We assume that user and assistant messages alternate.
    for i in range(0, len(history), 2):
        user_msg = ""
        ai_msg = ""
        if i < len(history) and history[i].get("role") == "user":
            user_msg = history[i].get("content", "")
        if i+1 < len(history) and history[i+1].get("role") == "assistant":
            ai_msg = history[i+1].get("content", "")
        chat_history += f"User: {user_msg}\nAI: {ai_msg}\n"
        
    prompt = f"""
        You are TutorBuddy, working for a courses company that specializes in web development, mobile development, data science, and machine learning courses. Your task is to assess the user's interests and generate a natural language search query for our semantic vector database to retrieve the most relevant course recommendations.

        Based on the following conversation history:
        {chat_history}

        And considering the following additional details:
        {additional_info}

        Instructions:
        1. Provide a concise search query in plain English that reflects the user's interests.
        2. Do not use any Boolean operators (such as OR, AND, NOT) or any complex punctuation—write a natural sentence.
        3. Only use topics within the following categories: web development, mobile development, data science, and machine learning.
        4. If no relevant context or details are found, simply return "intro to python course".
        5. Only return the search query text without any explanation.

        SEND SEARCH QUERY NOW:
        """
    response = tutor.log_and_invoke([{"role": "user", "content": prompt}], tool_name="generate_search_query_response")
    return response.content.strip()


def explain_concept_for_request(tutor, state, request) -> str:
    request_text = request.get("request_text", "")
    course = request.get("course", "")
    lesson = request.get("lesson", "")
    # Normalize lesson: if lesson is just a number, prepend "lesson "
    if lesson and not lesson.lower().startswith("lesson"):
        lesson = f"lesson {lesson}"
    # If reference history is set, prepend the referenced context
    if request.get("reference_history", False):
        history_idx = request.get("history_index", -1)
        history = state['history']
        if 0 <= history_idx < len(history):
            referenced_context = history[history_idx].get("input", "")
            request_text = f"{referenced_context} {request_text}"
    full_query = f"{course} {lesson} {request_text}"
    # Use the unified vector retriever
    context = tutor.vector_retriever.invoke(full_query)
    prompt = f"""
    You are a helpful tutor.
    Course: {course}
    Lesson: {lesson}
    Question: {request_text}
    Context:
    {context}
    
    Only explain what's in the context, not what's in the history.
    Now explain the concept clearly and thoroughly.
    """
    response = tutor.log_and_invoke([{"role": "user", "content": prompt}], tool_name="explain_concept_response")
    return response.content

def give_example_for_request(tutor, state, request) -> str:
    request_text = request.get("request_text", "")
    if request.get("reference_history", False):
        history_idx = request.get("history_index", -1)
        history = state['history']
        if 0 <= history_idx < len(history):
            referenced_context = history[history_idx].get("input", "")
            request_text = f"{referenced_context} {request_text}"
    # Use the unified vector retriever
    context = tutor.vector_retriever.invoke(request_text)
    prompt = f"""
    Give a code example for:
    {request_text}
    Context:
    {context}
    Provide a clear, well-commented code example that demonstrates the concept.
    """
    response = tutor.log_and_invoke([{"role": "user", "content": prompt}], tool_name="give_example_response")
    return response.content

def generate_quiz_for_request(tutor, state, request) -> str:
    request_text = request.get("request_text", "")
    course = request.get("course", "")
    lesson = request.get("lesson", "")
    full_query = f"{course} {lesson} {request_text}"
    # Retrieve context from the unified vector store
    context = tutor.vector_retriever.invoke(full_query)
    prompt = f"""
    You are a helpful tutor.
    
    Based on the following details:
    - Request: {request_text}
    - Course: {course}
    - Lesson: {lesson}
    - Retrieved Context: {context}
    
    Create a multiple-choice quiz question appropriate for the given course and lesson.
    The quiz should include a clear question, four options labeled A) through D), 
    and an indication of the correct answer.
    """
    response = tutor.log_and_invoke([{"role": "user", "content": prompt}], tool_name="simplify_concept_for_response")
    return response.content

def simplify_concept_for_request(tutor, state, request) -> str:
    request_text = request.get("request_text", "")
    prompt = f"Explain like I'm 5: {request_text}"
    response = tutor.log_and_invoke([{"role": "user", "content": prompt}], tool_name="simplify_concept_for_response")
    return response.content

def recommend_courses_for_request(tutor, state, request) -> str:
    request_text = request.get("request_text", "")
    completed_courses = state['completed_courses']

    # Generate a search query based on conversation history and the user's request.
    additional_info = f"User request: {request_text}"
    search_query = generate_search_query(tutor, state, additional_info)
    
    # Use the unified vector store for similarity search with a broader candidate set.
    docs = tutor.vectorstore.similarity_search(search_query, k=2) if tutor.vectorstore else []
    retrieved_courses = []
    for doc in docs:
        lines = doc.page_content.splitlines()
        if lines:
            # Extract the course title from the first line (assuming it starts with "Course:")
            course_title = lines[0].replace("Course:", "").strip()
            if course_title.lower() not in [c.lower() for c in completed_courses]:
                retrieved_courses.append((course_title, doc.page_content))
    
    # If we found at least one course, pick the top one; otherwise, default.
    if retrieved_courses:
        recommended_course_title, course_details = retrieved_courses[0]
    else:
        recommended_course_title = "Intro to Python"
        course_details = "Course: Intro to Python\nDescription: Beginner-friendly Python course."
    
    # Debug: print the retrieved course details.
    # print("Retrieved Course Details:", course_details)
    
    # Build a prompt that forces the LLM to recommend the retrieved course.
    prompt = f"""
    The user is interested in: {request_text}
    Completed courses: {completed_courses}
    Based on the following course details:
    {course_details}
    
    Recommend the course "{recommended_course_title}" and explain why it would be beneficial for the user.
    """
    response = tutor.log_and_invoke([{"role": "user", "content": prompt}], tool_name="recommend_courses_for_response")
    return response.content

def handle_course_completion_for_request(tutor, state, request) -> str:
    request_text = request.get("request_text", "")
    completed_courses = request.get("completed_courses", [])
    prompt = f"""
    The user has indicated they've completed some courses.
    Available courses: ["intro to python", "web dev with django", "data science with pandas", "machine learning basics"]
    User's message: "{request_text}"
    Courses that user wants to mark as completed: {completed_courses}
    Their current course list: {state.get('completed_courses', [])}
    
    Confirm which courses have been marked as completed and suggest a next step.
    """
    response = tutor.log_and_invoke([{"role": "user", "content": prompt}], tool_name="handle_course_completion_request")
    return response.content

def fallback_for_request(tutor, state, request) -> str:
    request_text = request.get("request_text", "")
    prompt = f"""
    Tell that to the user:
    I'm not sure I fully understand your question about: 
    "{request_text}"
    
    Could you please clarify what you're looking for? You can ask me to:
    - Explain a concept
    - Provide a code example
    - Generate a quiz question
    - Simplify a concept
    - Recommend a course
    """
    response = tutor.log_and_invoke([{"role": "user", "content": prompt}], tool_name="fallback_for_response")
    return response.content

def converse_for_request(tutor, state, request) -> str:
        context = state.get("context", "")
        chat_history = state.get("db_history", "")
        prompt = f"""
        User Conversation History:
        {chat_history}

        Context of the current conversation:
        {context}
        
        The user's latest input: {state['user_input']}
        
        Please generate a warm, engaging, and natural conversational response that continues the dialogue.
        """
        response = tutor.log_and_invoke([{"role": "user", "content": prompt}], tool_name="normale_conversation_response")
        return response.content
    
    

def pdf_search_for_request(tutor, state, request) -> str:
    """
    Uses the PDFSearchTool from crewai_tools to search within an uploaded PDF based on the user's query.
    
    The function expects the request object to include:
      - "request_text": the full latest user message.
      - "file_name": the original filename or file path of the referenced PDF.
    
    It retrieves the PDF's metadata from the session state and uses the stored configuration.
    """
    import os

    # Obtain the file name from the request. It might be empty.
    file_name = request.get("file_name", "").strip()
    request_text = request.get("request_text", "")

    pdf_info = None
    original_name = None

    # Debug: Print all files available in the state.
    available_files = state.get("files", {})
    # print("DEBUG: Files in session state:", list(available_files.keys()))

    # Look for the file info in the state["files"] dictionary.
    # The keys of state["files"] are assumed to be the file paths, e.g., "uploads/<uuid>.pdf".
    for key, file in available_files.items():
        # print(f"DEBUG: Checking key: {key}, original_filename in state: {file.get('original_filename')}")
        # Check if the provided file_name matches either the original filename
        # or the file path (which is the key) from the session.
        if file.get("original_filename") == file_name or key == file_name:
            pdf_info = file
            original_name = key  # key should be the file path, e.g. "uploads/..."
            # print("DEBUG: Found the file:", original_name)
            break

    # If no match was found and no file_name was provided, pick the first available file.
    if pdf_info is None:
        if not file_name and available_files:
            key, pdf_info = next(iter(available_files.items()))
            original_name = key
            # print("DEBUG: No file name provided; using first available file:", original_name)
        else:
            error_message = f"Error: File with name '{file_name}' not found in the session."
            # print("DEBUG:", error_message)
            return error_message

    # Ensure the file path uses the relative "./uploads/" format.
    # If original_name does not start with "./uploads/", adjust it accordingly.
    if not original_name.startswith("./uploads/"):
        if original_name.startswith("uploads/"):
            original_name = "./" + original_name
        else:
            original_name = "./uploads/" + original_name
    # print("DEBUG: Final file path used:", original_name)

    # Log the current working directory.
    # print("Current working directory:", current_path)

    # (Optional) Check if the file exists on disk.
    # Build an absolute path from the current path and the relative file path.
    # Remove any leading "./" from original_name before joining.

    # Retrieve the configuration stored in the file info.
    tool_config = pdf_info.get("tool_config")
    
    # Instantiate the PDFSearchTool with the existing configuration and file path.
    pdf_search_tool = PDFSearchTool(config=tool_config, pdf=original_name)
    
    # Perform the search using the request text.
    search_result = pdf_search_tool.run(request_text)
    logger.info("Search result completed for: %s", original_name)
    
    return search_result

