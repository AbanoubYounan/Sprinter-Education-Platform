from app.tutor_chain.config import logger

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
    context = tutor.lesson_retriever.invoke(full_query)
    prompt = f"""
    You are a helpful tutor.
    Course: {course}
    Lesson: {lesson}
    Question: {request_text}
    Context:
    {context}
    
    only explain whats in the context not whats in the history,
    Now explain the concept clearly and thoroughly.
    """
    response = tutor.log_and_invoke([{"role": "user", "content": prompt}])
    return response.content

def give_example_for_request(tutor, state, request) -> str:
    request_text = request.get("request_text", "")
    if request.get("reference_history", False):
        history_idx = request.get("history_index", -1)
        history = state['history']
        if 0 <= history_idx < len(history):
            referenced_context = history[history_idx].get("input", "")
            request_text = f"{referenced_context} {request_text}"
    context = tutor.lesson_retriever.invoke(request_text)
    prompt = f"""
    Give a code example for:
    {request_text}
    Context:
    {context}
    Provide a clear, well-commented code example that demonstrates the concept.
    """
    
    print()
    response = tutor.log_and_invoke([{"role": "user", "content": prompt}])
    return response.content

def generate_quiz_for_request(tutor, state, request) -> str:
    # Extract analyzer output
    request_text = request.get("request_text", "")
    course = request.get("course", "")
    lesson = request.get("lesson", "")
    
    # Build a full query that incorporates the analyzer's data
    full_query = f"{course} {lesson} {request_text}"
    # Retrieve context from the lesson vectorstore
    context = tutor.lesson_retriever.invoke(full_query)
    
    # Construct a prompt that uses both the analyzer output and retrieved context
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
    
    response = tutor.log_and_invoke([{"role": "user", "content": prompt}])
    return response.content


def simplify_concept_for_request(tutor, state, request) -> str:
    request_text = request.get("request_text", "")
    prompt = f"Explain like I'm 5: {request_text}"
    response = tutor.log_and_invoke([{"role": "user", "content": prompt}])
    return response.content

def recommend_courses_for_request(tutor, state, request) -> str:
    request_text = request.get("request_text", "")
    completed_courses = state['completed_courses']
    docs = tutor.course_vectorstore.similarity_search(request_text, k=5) if tutor.course_vectorstore else []
    available_courses = []
    for doc in docs:
        course_title = doc.page_content.split(" - ")[0].lower()
        if course_title not in completed_courses:
            available_courses.append(doc.page_content)
    docs_string = "\n".join(available_courses)
    prompt = f"""
    The user is interested in: {request_text}
    Completed courses: {completed_courses}
    Available courses:
    {docs_string}
    Recommend one or two courses and explain why they would be beneficial.
    """
    response = tutor.log_and_invoke([{"role": "user", "content": prompt}])
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
    response = tutor.log_and_invoke([{"role": "user", "content": prompt}])
    return response.content

def fallback_for_request(tutor, state, request) -> str:
    request_text = request.get("request_text", "")
    prompt = f"""
    I'm not sure I fully understand your question about: 
    "{request_text}"
    
    Could you please clarify what you're looking for? You can ask me to:
    - Explain a concept
    - Provide a code example
    - Generate a quiz question
    - Simplify a concept
    - Recommend a course
    """
    response = tutor.log_and_invoke([{"role": "user", "content": prompt}])
    return response.content
