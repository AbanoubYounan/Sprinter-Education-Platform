import re
import json
from app.tutor_chain.config import logger

def analyze_input_with_llm(tutor, state) -> dict:
    logger.debug("Analyzing input: %s", state['user_input'])
    text = state['user_input'].lower()
    exit_phrases = ["exit", "quit", "stop", "goodbye", "bye"]
    if any(phrase in text for phrase in exit_phrases):
        logger.info("User wants to exit the conversation.")
        return {"should_exit": True}

    history = state.get('db_history', [])[-10:] if state.get('db_history') else []
    chat_history = "\n".join(
        [f"User: {h['input']}\nAI: {h['response']}" for h in history]
    )
    prompt = f"""
    Given the user's message and recent chat history, analyze for MULTIPLE distinct requests/intents.
    Users often combine several questions or requests in one message and may reference previous conversations.
    Available courses: ['intro to python', 'web dev with django', 'data science with pandas', 'machine learning basics']
    Common interests: ['programming', 'web development', 'data science', 'machine learning', 'artificial intelligence', 'python']
    Possible intents: ['explanation', 'example', 'quiz', 'simplify', 'recommendation', 'course_completion', 'reference_history', 'fallback']
    Available tools: ExplainConcept, GiveExample, GenerateQuiz, SimplifyConcept, RecommendCourses, CourseCompletion, Fallback
    Recent Chat History:
    {chat_history}
    User message: "{text}"

    Instructions:
    1. Identify all separate actionable requests from the user’s message.
    2. Remove any duplicate phrases in the extracted request text.
    3. If the user mentions a current course they are working on, add a field "current_course" with the course name; otherwise, leave it empty.
    4. don't use Fallback unless the user's intent is not clear, if it's clear based on the context don't use it no matter what.
    4. Return your analysis strictly as a JSON object with these fields:

    {{
        "requests": [
            {{
                "request_id": "unique_id_1",
                "request_text": "extracted text for this specific request",
                "course": "course name or empty string",
                "lesson": "lesson number or empty string",
                "current_course": "current course name if mentioned, else empty string",
                "interests": ["list", "of", "interests"],
                "completed_courses": ["list", "of", "completed", "courses"],
                "intent": "one of the intent options",
                "tool": "one of the available tools",
                "reference_history": true or false,
                "history_index": -1 or index of referenced history item
            }}
        ]
    }}
    Make sure the response is valid JSON and nothing else.
    """
    
    response = tutor.log_and_invoke([{"role": "user", "content": prompt}])
    try:
        raw_response = response.content
        logger.debug(f"Raw LLM response: {raw_response}")
        json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
        if not json_match:
            raise ValueError("No JSON object found in the response")
        json_content = json_match.group(0)
        result = json.loads(json_content)
        requests = result.get("requests", [])
        for req in requests:
            original_text = req.get("request_text", "")
            words = original_text.split()
            deduped = []
            for word in words:
                if not deduped or word != deduped[-1]:
                    deduped.append(word)
            req["request_text"] = " ".join(deduped)
            if req.get("intent") == "course_completion" and req.get("tool") != "CourseCompletion":
                req["tool"] = "CourseCompletion"
            # Merge duplicate requests if needed.
        merged_requests = {}
        for req in requests:
            req_text = req.get("request_text", "").strip().lower()
            if req_text in merged_requests:
                existing = merged_requests[req_text]
                if existing["tool"] == "Fallback" and req["tool"] != "Fallback":
                    merged_requests[req_text] = req
                else:
                    existing["interests"] = list(set(existing.get("interests", []) + req.get("interests", [])))
                    existing["completed_courses"] = list(set(existing.get("completed_courses", []) + req.get("completed_courses", [])))
            else:
                merged_requests[req_text] = req
        merged_requests_list = list(merged_requests.values())
        return {
            "multi_requests": merged_requests_list,
            "agent_partial_responses": {req["request_id"]: [] for req in merged_requests_list},
            "agent_responses": {},
            "context_references": {req["request_id"]: {"reference_history": req.get("reference_history", False), "history_index": req.get("history_index", -1)} for req in merged_requests_list}
        }
    except Exception as e:
        logger.error(f"Error parsing LLM multi-request response: {e}")
        return {
            "multi_requests": [{
                "request_id": "req_fallback",
                "request_text": state['user_input'],
                "course": "",
                "lesson": "",
                "interests": [],
                "completed_courses": [],
                "intent": "fallback",
                "tool": "Fallback",
                "reference_history": False,
                "history_index": -1
            }],
            "agent_partial_responses": {"req_fallback": []},
            "agent_responses": {},
            "context_references": {"req_fallback": {"reference_history": False, "history_index": -1}}
        }

def update_user_profile(tutor, state) -> dict:
    updated_state = state.copy()
    for request in state.get('multi_requests', []):
        interests = request.get('interests', [])
        for interest in interests:
            if interest and interest not in updated_state["user_profile"]["interests"]:
                updated_state["user_profile"]["interests"].append(interest)
    for request in state.get('multi_requests', []):
        completed_courses = request.get('completed_courses', [])
        for course in completed_courses:
            course_name = course.lower().strip()
            if course_name not in updated_state["completed_courses"]:
                updated_state["completed_courses"].append(course_name)
    for request in state.get('multi_requests', []):
        if request.get('current_course'):
            updated_state["current_course"] = request.get('current_course')
    for request in state.get('multi_requests', []):
        if request.get('lesson'):
            updated_state["current_lesson"] = request.get('lesson')
    return updated_state

def execute_tools_for_requests(tutor, state) -> dict:
    updated_state = state.copy()
    requests = state.get('multi_requests', [])
    if not requests:
        return {**updated_state, "conversational_response": "I'm not sure what you're asking. Could you clarify your question?"}
    tool_functions = {
        "ExplainConcept": tutor.explain_concept_for_request,
        "GiveExample": tutor.give_example_for_request,
        "GenerateQuiz": tutor.generate_quiz_for_request,
        "SimplifyConcept": tutor.simplify_concept_for_request,
        "RecommendCourses": tutor.recommend_courses_for_request,
        "CourseCompletion": tutor.handle_course_completion_for_request,
        "Fallback": tutor.fallback_for_request
    }
    agent_responses = {}
    for request in requests:
        request_id = request.get("request_id")
        tool_name = request.get("tool", "Fallback")
        tool_func = tool_functions.get(tool_name, tutor.fallback_for_request)
        response = tool_func(tutor, state, request)
        agent_responses[request_id] = response
    updated_state["agent_responses"] = agent_responses
    return updated_state

def generate_conversational_response(tutor, state) -> dict:
    agent_responses = state.get('agent_responses', {})
    if not agent_responses:
        return {**state, "conversational_response": "I'm not sure what you're asking. Could you clarify your question?"}
    history = state.get('db_history', [])[-5:]
    chat_history = "\n".join([f"User: {h['input']}\nAI: {h['response']}" for h in history])
    combined_responses = []
    for request_id, response in agent_responses.items():
        request_info = next((r for r in state['multi_requests'] if r.get('request_id') == request_id), {})
        request_text = request_info.get('request_text', '')
        combined_responses.append(f"For question: '{request_text}'\nResponse: {response}")
    all_responses = "\n\n".join(combined_responses)
    prompt = f"""
    Conversation History:
    {chat_history}
    
    The user's latest question: {state['user_input']}
    
    I've prepared responses to different parts of the user's message:
    {all_responses}
    
    Please transform these separate responses into a natural, conversational response
    that flows well and addresses all the user's questions and requests coherently.
    If there's only one response, just make it conversational without mentioning separate parts.
    
    Make the response concise but complete, and seamlessly blend the information together.
    
    Notes:
    Note 1 : Never tell the user this is a conversational response or anything of what you're doing or your notes
    Note 2 : always and always tell the user the response only
    Note 3: dont say courrses name from your mind always say you data only referencing to the prepared responses.
    
    tell your response now: 
    """
    response = tutor.log_and_invoke([{"role": "user", "content": prompt}])
    return {**state, "conversational_response": response.content}

def log_interaction(tutor, state) -> dict:
    updated_state = state.copy()
    intent_summary = []
    tool_summary = []
    course_summary = []
    lesson_summary = []
    for request in state.get('multi_requests', []):
        intent_summary.append(request.get('intent', 'fallback'))
        tool_summary.append(request.get('tool', 'Fallback'))
        if request.get('course'):
            course_summary.append(request.get('course'))
        if request.get('lesson'):
            lesson_summary.append(request.get('lesson'))
    intent = ", ".join(set(intent_summary)) if intent_summary else "fallback"
    tool = ", ".join(set(tool_summary)) if tool_summary else "Fallback"
    course = ", ".join(set(course_summary)) if course_summary else state.get('current_course', '')
    lesson = ", ".join(set(lesson_summary)) if lesson_summary else state.get('current_lesson', '')
    updated_state['current_interaction'] = {
        "intent": intent,
        "tool": tool,
        "course": course,
        "lesson": lesson,
        "multi_requests": state.get('multi_requests', [])
    }
    if 'history' not in updated_state:
        updated_state['history'] = []
    updated_state['history'] = [{
        "input": state['user_input'],
        "response": state['conversational_response'],
        "intent": intent,
        "tool": tool, 
        "course": course,
        "lesson": lesson
    }]
    return updated_state
