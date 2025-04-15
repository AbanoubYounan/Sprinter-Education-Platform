import re
import json
import logging

logger = logging.getLogger(__name__)

def build_file_history_string(state: dict) -> str:
    """
    Constructs a dynamic file history string from the session state.
    It retrieves the 'files' key from the state and builds a formatted string
    listing each file and its summary.
    """
    user_files = state.get("files", {})
    file_history_lines = []
    for file_key, file_info in user_files.items():
        original_filename = file_info.get("original_filename", "Unknown File")
        summary_obj = file_info.get("summary", "No summary available")
        # If the summary is an object that has a "content" attribute, extract the text.
        if hasattr(summary_obj, "content"):
            summary_text = summary_obj.content.strip()
        else:
            summary_text = str(summary_obj).strip()
        file_history_lines.append(f'{original_filename}: {summary_text}')
    
    logger.info("File history lines: %s", "\n".join(file_history_lines) if file_history_lines else "No file history available.")
    return "\n".join(file_history_lines) if file_history_lines else "No file history available."


def retrieve_relevant_history(history, query, top_n=5):
    # Using the last top_n interactions as a placeholder.
    # Replace with a more sophisticated relevance-based filter if needed.
    relevant_history = history[-top_n:]
    return "\n".join(
        [f"User: {h['input']}\nAI: {h['response']}" for h in relevant_history]
    )

def analyze_input_with_llm(tutor, state) -> dict:
    # logger.info("stateeee in chain.py", state)
    logger.debug("Analyzing input: %s", state['user_input'])
    text = state['user_input'].lower()
    exit_phrases = ["exit", "quit", "stop", "goodbye", "bye"]
    if any(phrase in text for phrase in exit_phrases):
        logger.info("User wants to exit the conversation.")
        return {"should_exit": True}
    history = state.get('db_history', [])
    # Use retrieve_relevant_history for the last 10 interactions
    chat_history = retrieve_relevant_history(history, text, top_n=10)
    # print("chat history", chat_history)
    
    # Build dynamic file history using the helper function.
    file_history_dynamic = build_file_history_string(state)
    # print("FILE HISTROY" , file_history_dynamic)

    # Extended prompt with file search tool instructions.
    prompt = f"""
        You are TutorBuddy, a friendly, knowledgeable, and engaging tutor.
        Your goal is to assist the user with learning while keeping the conversation natural and warm.

        Given the user's message and recent chat history, analyze the input for multiple distinct actionable requests or conversational cues.
        Sometimes users may ask for a recommendation and then later indicate they have taken a course; in that case, output separate actionable requests for both:
        one for recommending a course and one for marking a course as completed.

        Available courses: ['intro to python', 'web dev with django', 'data science with pandas', 'machine learning basics']
        Common interests: ['programming', 'web development', 'data science', 'machine learning', 'artificial intelligence', 'python']
        Possible intents: ['explanation', 'example', 'quiz', 'simplify', 'recommendation', 'course_completion', 'reference_history', 'conversation', 'pdf_search']
        Available tools: ExplainConcept, GiveExample, GenerateQuiz, SimplifyConcept, RecommendCourses, CourseCompletion, Converse, pdfSearch
        User files:
        
        {file_history_dynamic}
        
        Recent Chat History:
        {chat_history}
        User message: "{text}"

        Instructions:
        1. Identify all separate actionable requests or conversational intents in the user's message and in the context of the chat history.
           - If the chat history shows that the user previously requested a course recommendation and the latest message is about course completion (for example, "I took Intro to Python"), then output two separate request objects:
               a. One for recommending a course (intent "recommendation", tool "RecommendCourses").
               b. One for course completion (intent "course_completion", tool "CourseCompletion").
        2. **For every request object, use the entire latest user message (i.e. "{text}") as the value for the "request_text" field.**
        3. Remove any duplicate phrases in the extracted request text.
        4. If the user mentions a current course they are working on, add a field "current_course" with the course name; otherwise, leave it empty.
        5. If no clear actionable request is detected, treat the input as a general conversation and mark the intent as "conversation" using the tool "Converse".
        6. For recommendation requests:
           - Mark the intent as "recommendation" and set the tool as "RecommendCourses".
           - Only include the "interests" field if the user explicitly states that they like a particular field or mentions seeing a course in that field.
        7. For file-related queries:
           - If the user's query is referencing or is clearly derived from one of the files the user has uploaded (e.g. "search in [file name]", "what does [file name] say", etc.),
             mark the intent as "pdf_search" and set the tool as "pdfSearch".
           - In this case, include an additional field "file_name" which should be the original filename of the file being referenced.
           - in case the user asked for explenation that only exists in the pdf the tool will be pdfSearch not ExplainConcept as ExplainConcept is only for the courses data
        8. Return your analysis strictly as a JSON object with these fields:

        {{
            "requests": [
                {{
                    "request_id": "unique_id_1",
                    "request_text": "extracted text for this specific request or conversational response",
                    "course": "course name or empty string",
                    "lesson": "lesson number or empty string",
                    "current_course": "current course name if mentioned, else empty string",
                    "interests": ["list", "of", "interests"],
                    "completed_courses": ["list", "of", "completed", "courses"],
                    "intent": "one of the intent options (if no actionable request, use 'conversation' or 'pdf_search' for file queries)",
                    "tool": "one of the available tools (if no actionable request, use 'Converse'; for file queries, use 'pdfSearch')",
                    "file_name": "file name if applicable, otherwise empty string",
                    "reference_history": true or false,
                    "history_index": -1 or index of referenced history item
                }},
                {{ 
                    ... additional request objects if multiple actionable requests are detected ...
                }}
            ]
        }}
        Make sure the response is valid JSON and nothing else.
    """
    
    response = tutor.log_and_invoke([{"role": "user", "content": prompt}], tool_name="analyze_input_with_llm")
    try:
        raw_response = response.content
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
        
        # Do not merge requests; return all as-is.
        merged_requests_list = requests
        
        return {
            "multi_requests": merged_requests_list,
            "agent_partial_responses": {req["request_id"]: [] for req in merged_requests_list},
            "agent_responses": {},
            "context_references": {
                req["request_id"]: {
                    "reference_history": req.get("reference_history", False),
                    "history_index": req.get("history_index", -1)
                }
                for req in merged_requests_list
            }
        }
    except Exception as e:
        logger.error(f"Error parsing LLM multi-request response: {e}")
        # Fallback to a default conversational request.
        return {
            "multi_requests": [{
                "request_id": "req_converse",
                "request_text": state['user_input'],
                "course": "",
                "lesson": "",
                "current_course": "",
                "interests": [],
                "completed_courses": [],
                "intent": "conversation",
                "tool": "Converse",
                "file_name": "",
                "reference_history": False,
                "history_index": -1
            }],
            "agent_partial_responses": {"req_converse": []},
            "agent_responses": {},
            "context_references": {"req_converse": {"reference_history": False, "history_index": -1}}
        }

def build_context_node(tutor, state) -> dict:
    # Get the conversation history and current query
    history = state.get('db_history', [])
    current_query = state.get('user_input', "")
    
    # Use retrieve_relevant_history to extract the most pertinent parts (using top 5 interactions)
    context_history = retrieve_relevant_history(history, current_query, top_n=5)
    
    # Build the initial context string with the relevant history and current input
    initial_context = f"Relevant Conversation History:\n{context_history}\n\nUser's Current Input: {current_query}\n"
    
    # print(initial_context)
    
    # Build a prompt that instructs the LLM to filter out redundant details,
    # returning only the important context needed to answer the query.
    refined_prompt = f"""
    You are an assistant specialized in summarizing conversation context.
    
    Given the following conversation context, please extract only the essential details that are necessary to answer the user's query.
    Do not include any unnecessary or redundant information.
    extract only what the user want.
    You'll find a conversation between the user and his current query based on both extract what the user wants now only and if there is unfifiled requests that needs to be fulfilled still based on his query if he's asking for it
    
    Conversation Context:
    {initial_context}
    
    Return only the refined context now.
    """
    # Invoke the LLM with the prompt to obtain the refined context.
    response = tutor.log_and_invoke([{"role": "user", "content": refined_prompt}], tool_name="build_context_node")
    refined_context = response.content.strip()
    
    # Update the state with the refined context.
    state["context"] = refined_context
    return state

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
        # Generate a friendly conversational response using the Converse tool.
        return {
            **updated_state, 
            "conversational_response": tutor.converse_for_request(
                tutor, 
                state, 
                {"request_text": state['user_input']}
            )
        }
    
    tool_functions = {
        "ExplainConcept": tutor.explain_concept_for_request,
        "GiveExample": tutor.give_example_for_request,
        "GenerateQuiz": tutor.generate_quiz_for_request,
        "SimplifyConcept": tutor.simplify_concept_for_request,
        "RecommendCourses": tutor.recommend_courses_for_request,
        "CourseCompletion": tutor.handle_course_completion_for_request,
        "Converse": tutor.converse_for_request,
        "pdfSearch": tutor.pdf_search_for_request
    }
    
    agent_responses = {}
    for req in requests:
        request_id = req.get("request_id")
        tool_name = req.get("tool", "Converse")
        tool_func = tool_functions.get(tool_name, tutor.converse_for_request)
        response = tool_func(tutor, state, req)
        agent_responses[request_id] = response
        # print("response", response)
    updated_state["agent_responses"] = agent_responses
    return updated_state


def generate_conversational_response(tutor, state) -> dict:
    # Use the refined context stored in state["context"]
    context = state.get("context", "")
    agent_responses = state.get('agent_responses', {})
    if not agent_responses:
        return {**state, "conversational_response": f"{context}\nI'm not sure what you're asking. Could you clarify your question?"}
    
    combined_responses = []
    for request_id, response in agent_responses.items():
        request_info = next((r for r in state['multi_requests'] if r.get('request_id') == request_id), {})
        request_text = request_info.get('request_text', '')
        combined_responses.append(f"For question: '{request_text}'\nResponse: {response}")
    all_responses = "\n\n".join(combined_responses)
    
    # Revised prompt instructing the LLM to only output the final answer
    prompt = f"""
    {context}

    I've prepared responses to different parts of your message:
    {all_responses}

    Based on the above, please generate a natural, conversational response that flows well and addresses all of the user's questions.
    IMPORTANT: Do not repeat or include any of the conversation context or internal notes. Return only your final answer.
    Final Answer:
    """
    response = tutor.log_and_invoke(
        [{"role": "user", "content": prompt}],
        tool_name="generate_conversational_response"
    )
    final_response = response.content.strip()
    return {**state, "conversational_response": final_response}

 
def log_interaction(tutor, state) -> dict:
    updated_state = state.copy()
    intent_summary = []
    tool_summary = []
    course_summary = []
    lesson_summary = []
    for request in state.get('multi_requests', []):
        intent_summary.append(request.get('intent', 'conversation'))
        tool_summary.append(request.get('tool', 'Converse'))
        if request.get('course'):
            course_summary.append(request.get('course'))
        if request.get('lesson'):
            lesson_summary.append(request.get('lesson'))
    intent = ", ".join(set(intent_summary)) if intent_summary else "conversation"
    tool = ", ".join(set(tool_summary)) if tool_summary else "Converse"
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
