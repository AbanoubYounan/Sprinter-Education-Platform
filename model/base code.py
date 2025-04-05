from langchain.chat_models import ChatOpenAI
from langchain.agents import Tool
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import CharacterTextSplitter
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
import os, json
from typing import TypedDict, List, Dict, Any, Tuple
from langchain_core.runnables import chain
from langgraph.graph import StateGraph, END
import functools
import logging
from langchain.llms.base import LLM
import re
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG to capture detailed logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Get logger for your module
logger = logging.getLogger(__name__)

# Suppress noisy logs from dependencies
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('openai').setLevel(logging.WARNING)


def log_and_invoke(llm: LLM, messages, **kwargs):
    # Log the prompt (the actual message content being sent to the LLM)
    # logging.debug("Sending prompt to LLM: %s", messages)
    
    # Invoke the LLM and get the response
    response = llm.invoke(messages, **kwargs)
    logging.debug("Raw LLM response: %s", response.content)
    # Log the response content (can be useful for debugging)
    # if hasattr(response, "usage"):
    #     logging.debug("Token usage: %s", response.usage)
    # logging.debug("LLM response: %s", response.content)
    
    return response

# API keys setup
os.environ["OPENAI_API_KEY"] = "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"
os.environ["OPENAI_API_BASE"] = "https://api.groq.com/openai/v1"

# Setup LLM
llm = ChatOpenAI(
    model="llama3-70b-8192",
    temperature=0.5,
    max_tokens=400  # Increased token limit for more detailed responses
)

# Google Gemini API for embeddings
def get_embedding_model():
    """Use Google's Gemini embeddings or fall back to alternatives"""
    try:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        os.environ["GOOGLE_API_KEY"] = "AIzaSyDFhJYHU1GTnOottGuJqnVJH81rESYwZJI"
        return GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    except Exception as e:
        print(f"Google Gemini embeddings failed: {e}")
        class SimpleKeywordEmbedding:
            def embed_documents(self, texts):
                return [[0.1] * 5 for _ in texts]
            def embed_query(self, text):
                return [0.1] * 5
        print("Using simple keyword matching as fallback")
        return SimpleKeywordEmbedding()

# Use the fallback-enabled embedding function
embedding = get_embedding_model()

course_library = {
    "data science with pandas": {
        "lessons": {
            "lesson 1": "Intro to Pandas, DataFrames and Series, basic operations.",
            "lesson 2": "Reading CSVs, indexing, filtering, and groupby operations."
        }
    },
    "web dev with django": {
        "lessons": {
            "lesson 1": {"title" : "Django setup, project structure, and development server."},
            "lesson 2": "Django views, URLs, and templates explained in detail."
        }
    }
}

courses = [
    {"title": "Intro to Python", "desc": "Beginner-friendly Python course."},
    {"title": "Web Dev with Django", "desc": "Build full-stack web apps with Django."},
    {"title": "Data Science with Pandas", "desc": "Analyze data using Pandas & NumPy."},
    {"title": "Machine Learning Basics", "desc": "Learn ML with Scikit-learn and Python."}
]

course_texts = [f"{c['title']} - {c['desc']}" for c in courses]

# Initialize vectorstores to None, we'll create them lazily when needed
lesson_vectorstore = None
lesson_retriever = None
course_vectorstore = None

def init_vectorstores():
    """Initialize the vectorstores only when needed"""
    global lesson_vectorstore, lesson_retriever, course_vectorstore
    if lesson_vectorstore is None:
        all_lessons = []
        for course, data in course_library.items():
            for lesson_id, lesson_content in data["lessons"].items():
                if isinstance(lesson_content, dict):
                    lesson_text = lesson_content.get("title", "")
                else:
                    lesson_text = lesson_content
                all_lessons.append({
                    "text": lesson_text,
                    "course": course,
                    "lesson": lesson_id
                })
        lesson_texts = [lesson["text"] for lesson in all_lessons]
        text_splitter = CharacterTextSplitter(chunk_size=200, chunk_overlap=20)
        chunks = []
        for i, text in enumerate(lesson_texts):
            text_chunks = text_splitter.split_text(text)
            for chunk in text_chunks:
                chunks.append({
                    "text": chunk,
                    "course": all_lessons[i]["course"],
                    "lesson": all_lessons[i]["lesson"]
                })
        chunk_texts = [chunk["text"] for chunk in chunks]
        try:
            lesson_vectorstore = FAISS.from_texts(chunk_texts, embedding)
            lesson_retriever = lesson_vectorstore.as_retriever()
        except Exception as e:
            print(f"Failed to create lesson vectorstore: {e}")
            def simple_retriever(query):
                query = query.lower()
                matches = []
                for chunk in chunks:
                    text = chunk["text"].lower()
                    if any(word in text for word in query.split()):
                        matches.append(chunk["text"])
                return matches[0] if matches else "No specific context available."
            lesson_retriever = lambda q: simple_retriever(q)
    if course_vectorstore is None:
        try:
            course_vectorstore = FAISS.from_texts(course_texts, embedding)
        except Exception as e:
            print(f"Failed to create course vectorstore: {e}")
            course_vectorstore = None

class TutorState(TypedDict):
    user_profile: Dict[str, Any]
    current_course: str
    current_lesson: str
    history: List[Dict[str, str]]  # This will store the conversation history
    completed_courses: List[str]
    user_input: str
    analysis: Dict[str, Any]
    multi_requests: List[Dict[str, Any]]  # New field for multiple detected requests
    agent_responses: Dict[str, str]  # Map request IDs to responses
    agent_partial_responses: Dict[str, List[str]]  # Map request IDs to partial responses
    conversational_response: str
    context_references: Dict[str, Any]  # References to previous conversation context
    

# Enhanced analysis to detect multiple requests
def analyze_input_with_llm(state: TutorState) -> Dict:
    """Use LLM to analyze user input and determine multiple requests/intents"""
    logging.debug("Analyzing input: %s", state['user_input'])
    text = state['user_input'].lower()
    # Check for exit conditions first
    exit_phrases = ["exit", "quit", "stop", "goodbye", "bye"]
    if any(phrase in text for phrase in exit_phrases):
        logging.info("User wants to exit the conversation.")
        return {"should_exit": True}

    # Get the last 5 interactions from history
    history = state['history'][-5:] if state['history'] else []
    chat_history = "\n".join([f"User: {h['input']}\nAI: {h['response']}" for h in history])
    
    course_options = ["intro to python", "web dev with django", "data science with pandas", "machine learning basics"]
    interest_options = ["programming", "web development", "data science", "machine learning", "artificial intelligence", "python"]
    intent_options = [
        "explanation - user wants a concept explained",
        "example - user wants an example",
        "quiz - user wants to be quizzed",
        "simplify - user wants a simpler explanation",
        "recommendation - user wants course recommendations",
        "course_completion - user is indicating they've completed course(s)",
        "reference_history - user refers to a previous request or context",
        "fallback - intent is unclear"
    ]

    prompt = f"""
    Given the user's message and recent chat history, analyze for MULTIPLE distinct requests/intents.
    Users often combine several questions or requests in one message, or refer to previous conversations.
    Available courses: {course_options}
    Common interests: {interest_options}
    Possible intents: {intent_options}
    Recent Chat History:
    {chat_history}
    User message: "{text}"
    First, identify if the user is referring to any previous conversation or question.
    Then, identify ALL separate questions or requests in the message.
    Return your analysis STRICTLY as a JSON object with these fields:
    {{
        "requests": [
            {{
                "request_id": "unique_id_1",  
                "request_text": "extracted text for this specific request",
                "course": "course name or empty string",
                "lesson": "lesson number or empty string",
                "interests": ["list", "of", "interests"],
                "completed_courses": ["list", "of", "completed", "courses"],
                "intent": "one of the intent options",
                "tool": "ExplainConcept/GiveExample/GenerateQuiz/SimplifyConcept/RecommendCourses/CourseCompletion/Fallback",
                "reference_history": true or false,
                "history_index": -1 or index of referenced history item
            }},
            {{
                "request_id": "unique_id_2",
                ... another request ...
            }}
        ]
    }}
    Make sure the response is valid JSON and nothing else.
    """
    logging.debug("Sending multi-request prompt to LLM")
    response = log_and_invoke(llm, [{"role": "user", "content": prompt}])

    try:
        # Extract only the JSON portion of the response
        raw_response = response.content
        logging.debug(f"Raw LLM response: {raw_response}")

        # Use regex to extract JSON content
        json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
        if not json_match:
            raise ValueError("No JSON object found in the response")

        json_content = json_match.group(0)
        result = json.loads(json_content)

        requests = result.get("requests", [])
        logging.debug(f"LLM detected {len(requests)} requests")

        # Ensure each request has a unique ID
        for i, req in enumerate(requests):
            if "request_id" not in req:
                req["request_id"] = f"req_{i}"

        return {
            "multi_requests": requests,
            "agent_partial_responses": {req["request_id"]: [] for req in requests},
            "agent_responses": {},
            "context_references": {
                req["request_id"]: {
                    "reference_history": req.get("reference_history", False),
                    "history_index": req.get("history_index", -1)
                } for req in requests
            }
        }

    except Exception as e:
        logging.error(f"Error parsing LLM multi-request response: {e}")
        # Fallback to single request
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

# Function to execute tool for each request
def execute_tools_for_requests(state: TutorState) -> Dict:
    """Process each request with its appropriate tool"""
    updated_state = state.copy()
    requests = state.get('multi_requests', [])
    
    if not requests:
        logging.warning("No requests to process")
        return {
            **updated_state,
            "conversational_response": "I'm not sure what you're asking. Could you clarify your question?"
        }
    
    # Define tool functions
    tool_functions = {
        "ExplainConcept": explain_concept_for_request,
        "GiveExample": give_example_for_request,
        "GenerateQuiz": generate_quiz_for_request,
        "SimplifyConcept": simplify_concept_for_request,
        "RecommendCourses": recommend_courses_for_request,
        "CourseCompletion": handle_course_completion_for_request,
        "Fallback": fallback_for_request
    }
    
    # Process each request with the appropriate tool
    agent_responses = {}
    
    for request in requests:
        request_id = request.get("request_id")
        tool_name = request.get("tool", "Fallback")
        tool_func = tool_functions.get(tool_name, fallback_for_request)
        
        # Execute the tool and get the response
        response = tool_func(state, request)
        agent_responses[request_id] = response
        
    updated_state["agent_responses"] = agent_responses
    return updated_state

def explain_concept_for_request(state: TutorState, request: Dict) -> str:
    """Explain a concept for a specific request"""
    request_text = request.get("request_text", "")
    course = request.get("course", "")
    lesson = request.get("lesson", "")
    
    # Handle history references if applicable
    if request.get("reference_history", False):
        history_idx = request.get("history_index", -1)
        history = state['history']
        if 0 <= history_idx < len(history):
            referenced_context = history[history_idx].get("input", "")
            request_text = f"{referenced_context} {request_text}"
    
    context = lesson_retriever.invoke(request_text)
    
    prompt = f"""
    You are a helpful tutor.
    Course: {course}
    Lesson: {lesson}
    Question: {request_text}
    Context:
    {context}
    Now explain the concept clearly and thoroughly.
    """
    response = log_and_invoke(llm, [{"role": "user", "content": prompt}])
    return response.content

def give_example_for_request(state: TutorState, request: Dict) -> str:
    """Give an example for a specific request"""
    request_text = request.get("request_text", "")
    
    # Handle history references
    if request.get("reference_history", False):
        history_idx = request.get("history_index", -1)
        history = state['history']
        if 0 <= history_idx < len(history):
            referenced_context = history[history_idx].get("input", "")
            request_text = f"{referenced_context} {request_text}"
    
    context = lesson_retriever.invoke(request_text)
    
    prompt = f"""
    Give a code example for:
    {request_text}
    Context:
    {context}
    Provide a clear, well-commented code example that demonstrates the concept.
    """
    response = log_and_invoke(llm, [{"role": "user", "content": prompt}])
    return response.content

def generate_quiz_for_request(state: TutorState, request: Dict) -> str:
    """Generate a quiz question for a specific request"""
    request_text = request.get("request_text", "")
    context = lesson_retriever.invoke(request_text)
    
    prompt = f"""
    Create a quiz question for:
    {request_text}
    Context:
    {context}
    Include both the question and the answer.
    """
    response = log_and_invoke(llm, [{"role": "user", "content": prompt}])
    return response.content

def simplify_concept_for_request(state: TutorState, request: Dict) -> str:
    """Simplify a concept for a specific request"""
    request_text = request.get("request_text", "")
    
    prompt = f"Explain like I'm 5: {request_text}"
    response = log_and_invoke(llm, [{"role": "user", "content": prompt}])
    return response.content

def recommend_courses_for_request(state: TutorState, request: Dict) -> str:
    """Recommend courses for a specific request"""
    request_text = request.get("request_text", "")
    completed_courses = state['completed_courses']

    # Get documents from vectorstore
    docs = course_vectorstore.similarity_search(request_text, k=5)
    # Filter out completed courses
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
    response = log_and_invoke(llm, [{"role": "user", "content": prompt}])
    return response.content

def handle_course_completion_for_request(state: TutorState, request: Dict) -> str:
    """Handle course completion for a specific request"""
    request_text = request.get("request_text", "")
    completed_courses = request.get("completed_courses", [])
    
    prompt = f"""
    The user has indicated they've completed some courses.
    Available courses: ["intro to python", "web dev with django", "data science with pandas", "machine learning basics"]
    User's message: "{request_text}"
    Courses that user want to mark as completed: {completed_courses}
    
    Confirm which courses have been marked as completed and suggest a next step.
    """
    response = log_and_invoke(llm, [{"role": "user", "content": prompt}])
    
    # Update the completed courses in the state
    for course in completed_courses:
        course_name = course.lower().strip()
        if course_name not in state["completed_courses"]:
            state["completed_courses"].append(course_name)
    
    return response.content

def fallback_for_request(state: TutorState, request: Dict) -> str:
    """Fallback for a specific request"""
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
    response = log_and_invoke(llm, [{"role": "user", "content": prompt}])
    return response.content

def generate_conversational_response(state: TutorState) -> Dict:
    """Generate a unified conversational response for all requests"""
    agent_responses = state.get('agent_responses', {})
    
    if not agent_responses:
        return {
            **state,
            "conversational_response": "I'm not sure what you're asking. Could you clarify your question?"
        }
    
    # Get the last few interactions from history
    history = state.get('history', [])[-3:]
    chat_history = "\n".join([f"User: {h['input']}\nAI: {h['response']}" for h in history])
    
    # Combine all request-specific responses
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
    Note 2 : alway and always tell the user the response only
    
    tell your response now: 
    """
    
    response = log_and_invoke(llm, [{"role": "user", "content": prompt}])
    
    return {
        **state,
        "conversational_response": response.content
    }

def update_user_profile(state: TutorState) -> Dict:
    """Update the user profile based on detected interests and completed courses"""
    updated_state = state.copy()
    
    # Extract and update interests
    for request in state.get('multi_requests', []):
        interests = request.get('interests', [])
        for interest in interests:
            if interest and interest not in updated_state["user_profile"]["interests"]:
                updated_state["user_profile"]["interests"].append(interest)
    
    # Mark courses as completed
    for request in state.get('multi_requests', []):
        completed_courses = request.get('completed_courses', [])
        for course in completed_courses:
            course_name = course.lower().strip()
            if course_name not in updated_state["completed_courses"]:
                updated_state["completed_courses"].append(course_name)
    
    return updated_state

def log_interaction(state: TutorState) -> Dict:
    """Log both user input and AI response for future reference"""
    updated_state = state.copy()
    
    # Ensure history exists
    if 'history' not in updated_state:
        updated_state['history'] = []
    
    # Extract key information from multi-requests
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
    
    # Combine into single entries or use the first one
    intent = ", ".join(set(intent_summary)) if intent_summary else "fallback"
    tool = ", ".join(set(tool_summary)) if tool_summary else "Fallback"
    course = ", ".join(set(course_summary)) if course_summary else state.get('current_course', '')
    lesson = ", ".join(set(lesson_summary)) if lesson_summary else state.get('current_lesson', '')
    
    # Add the current interaction
    updated_state['history'].append({
        "input": state['user_input'],
        "response": state['conversational_response'],
        "intent": intent,
        "tool": tool,
        "course": course,
        "lesson": lesson,
        "multi_requests": state.get('multi_requests', [])  # Store all request data for future reference
    })
    
    # Keep only the last 10 interactions (increased from 5)
    updated_state['history'] = updated_state['history'][-10:]
    
    return updated_state

# Workflow definition
workflow = StateGraph(TutorState)

# Add nodes
workflow.add_node("analyze_input", analyze_input_with_llm)
workflow.add_node("update_profile", update_user_profile)
workflow.add_node("execute_tools", execute_tools_for_requests)
workflow.add_node("generate_response", generate_conversational_response)
workflow.add_node("log_interaction", log_interaction)

# Set up edges
workflow.add_edge("analyze_input", "update_profile")
workflow.add_edge("update_profile", "execute_tools")
workflow.add_edge("execute_tools", "generate_response")
workflow.add_edge("generate_response", "log_interaction")
workflow.add_edge("log_interaction", END)

# Define conditional edges
def should_continue(state):
    if state.get("should_exit", False):
        return "end"
    return "continue"

workflow.add_conditional_edges(
    "analyze_input",
    should_continue,
    {
        "continue": "update_profile",
        "end": END
    }
)

# Set entry point
workflow.set_entry_point("analyze_input")

# Compile the graph
tutor_chain = workflow.compile()

# Initialize state and vectorstores
print("🤖 Enhanced AI Tutor is ready! Type 'exit' to quit.")
init_vectorstores()

# Initialize state with history
state = {
    "user_profile": {"name": None, "interests": []},
    "current_course": "",
    "current_lesson": "",
    "history": [],
    "completed_courses": [],
    "user_input": "",
    "multi_requests": [],
    "agent_responses": {},
    "agent_partial_responses": {},
    "conversational_response": "",
    "context_references": {},
    "should_exit": False
}

# Main loop
while True:
    user_input = input("\nYou: ").strip()
    if user_input.lower() in ["exit", "quit", "stop", "goodbye", "bye"]:
        print("👋 Goodbye!")
        break

    # Update the state with new user input while preserving history
    state.update({
        "user_input": user_input,
        "multi_requests": [],
        "agent_responses": {},
        "agent_partial_responses": {},
        "conversational_response": "",
        "context_references": {},
        "should_exit": False
    })

    try:
        # Invoke the chain with the current state (which includes history)
        results = tutor_chain.invoke(state)
        
        # Update the state with the results (including updated history)
        state.update(results)
        
        if 'conversational_response' in results:
            print(f"AI: {results['conversational_response']}")
        else:
            print("AI: I didn't get a response. Please try again.")
    except Exception as e:
        logger.error(f"Error: {e}")
        print("Sorry, I encountered an error. Please try again.")