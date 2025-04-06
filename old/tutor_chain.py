import os
import json
import re
import logging
from typing import Any, Dict, List, TypedDict

from langchain.chat_models import ChatOpenAI
from langchain.llms.base import LLM
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langgraph.graph import StateGraph, END

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('openai').setLevel(logging.WARNING)

# Define a TypedDict for our tutor state
class TutorState(TypedDict):
    user_profile: Dict[str, Any]
    current_course: str
    current_lesson: str
    history: List[Dict[str, str]]
    completed_courses: List[str]
    user_input: str
    analysis: Dict[str, Any]
    multi_requests: List[Dict[str, Any]]
    agent_responses: Dict[str, str]
    agent_partial_responses: Dict[str, List[str]]
    conversational_response: str
    context_references: Dict[str, Any]
    db_history: str
    should_exit: bool

class TutorChain:
    def __init__(self):
        # Set up API keys and LLM
        os.environ["OPENAI_API_KEY"] = "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"
        os.environ["OPENAI_API_BASE"] = "https://api.groq.com/openai/v1"
        self.llm = ChatOpenAI(
            model="llama3-70b-8192",
            temperature=0.5,
            max_tokens=400
        )
        self.embedding = self.get_embedding_model()

        # Sample course library and courses
        self.course_library = {
            "data science with pandas": {
                "lessons": {
                    "lesson 1": "Intro to Pandas, DataFrames and Series, basic operations.",
                    "lesson 2": "Reading CSVs, indexing, filtering, and groupby operations."
                }
            },
            "web dev with django": {
                "lessons": {
                    "lesson 1": {"title" : "Django setup, project structure, and development server."},
                    "lesson 2": {"title": "Django views, URLs, and templates explained in detail."}
                }
            }
        }
        self.courses = [
            {"title": "Intro to Python", "desc": "Beginner-friendly Python course."},
            {"title": "Web Dev with Django", "desc": "Build full-stack web apps with Django."},
            {"title": "Data Science with Pandas", "desc": "Analyze data using Pandas & NumPy."},
            {"title": "Machine Learning Basics", "desc": "Learn ML with Scikit-learn and Python."}
        ]
        self.course_texts = [f"{c['title']} - {c['desc']}" for c in self.courses]

        # Initialize vectorstores
        self.lesson_vectorstore = None
        self.lesson_retriever = None
        self.course_vectorstore = None
        self.init_vectorstores()

        # Build the workflow chain using StateGraph
        self.workflow = StateGraph(TutorState)
        self.workflow.add_node("analyze_input", self.analyze_input_with_llm)
        self.workflow.add_node("update_profile", self.update_user_profile)
        self.workflow.add_node("execute_tools", self.execute_tools_for_requests)
        self.workflow.add_node("generate_response", self.generate_conversational_response)
        self.workflow.add_node("log_interaction", self.log_interaction)
        self.workflow.add_edge("analyze_input", "update_profile")
        self.workflow.add_edge("update_profile", "execute_tools")
        self.workflow.add_edge("execute_tools", "generate_response")
        self.workflow.add_edge("generate_response", "log_interaction")
        self.workflow.add_edge("log_interaction", END)
        self.workflow.add_conditional_edges("analyze_input", self.should_continue, {"continue": "update_profile", "end": END})
        self.workflow.set_entry_point("analyze_input")
        self.tutor_chain = self.workflow.compile()

    def should_continue(self, state: TutorState) -> str:
        """
        Determine whether to continue the workflow or end it based on the state.
        
        Args:
            state (TutorState): The current state of the tutor
            
        Returns:
            str: 'continue' to proceed with the workflow, 'end' to terminate it
        """
        if state.get('should_exit', False):
            logger.info("Chain exiting based on should_exit flag")
            return "end"
        return "continue"

    def get_embedding_model(self):
        try:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            os.environ["GOOGLE_API_KEY"] = "AIzaSyDFhJYHU1GTnOottGuJqnVJH81rESYwZJI"
            return GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        except Exception as e:
            logger.error(f"Google Gemini embeddings failed: {e}")
            class SimpleKeywordEmbedding:
                def embed_documents(self, texts):
                    return [[0.1] * 5 for _ in texts]
                def embed_query(self, text):
                    return [0.1] * 5
            logger.info("Using simple keyword matching as fallback")
            return SimpleKeywordEmbedding()

    def init_vectorstores(self):
        if self.lesson_vectorstore is None:
            all_lessons = []
            for course, data in self.course_library.items():
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
                self.lesson_vectorstore = FAISS.from_texts(chunk_texts, self.embedding)
                self.lesson_retriever = self.lesson_vectorstore.as_retriever()
            except Exception as e:
                logger.error(f"Failed to create lesson vectorstore: {e}")
                def simple_retriever(query):
                    query = query.lower()
                    matches = []
                    for chunk in chunks:
                        text = chunk["text"].lower()
                        if any(word in text for word in query.split()):
                            matches.append(chunk["text"])
                    return matches[0] if matches else "No specific context available."
                self.lesson_retriever = lambda q: simple_retriever(q)
        if self.course_vectorstore is None:
            try:
                self.course_vectorstore = FAISS.from_texts(self.course_texts, self.embedding)
            except Exception as e:
                logger.error(f"Failed to create course vectorstore: {e}")
                self.course_vectorstore = None

    def log_and_invoke(self, messages, **kwargs):
        response = self.llm.invoke(messages, **kwargs)
        logger.debug("Raw LLM response: %s", response.content)
        return response

    # Chain step functions
    def analyze_input_with_llm(self, state: TutorState) -> dict:
        logger.debug("Analyzing input: %s", state['user_input'])
        text = state['user_input'].lower()
        exit_phrases = ["exit", "quit", "stop", "goodbye", "bye"]
        if any(phrase in text for phrase in exit_phrases):
            logger.info("User wants to exit the conversation.")
            return {"should_exit": True}

        # Use conversation history from the DB (assumed stored in 'db_history')
        history = state.get('db_history', [])[-10:] if state.get('db_history') else []
        chat_history = "\n".join(
            [f"User: {h['input']}\nAI: {h['response']}" for h in history]
        )
        # Updated prompt: ask the LLM to remove duplicate phrases and ensure tool/intent consistency.
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
        
        response = self.log_and_invoke([{"role": "user", "content": prompt}])
        try:
            raw_response = response.content
            logger.debug(f"Raw LLM response: {raw_response}")
            json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON object found in the response")
            json_content = json_match.group(0)
            result = json.loads(json_content)
            requests = result.get("requests", [])

            # Post-process the requests to remove repeated phrases from request_text.
            for req in requests:
                original_text = req.get("request_text", "")
                # Simple deduplication: split words and remove consecutive duplicates.
                words = original_text.split()
                deduped = []
                for word in words:
                    if not deduped or word != deduped[-1]:
                        deduped.append(word)
                req["request_text"] = " ".join(deduped)
                
                # Ensure tool and intent consistency:
                # If intent is course_completion, force tool to be CourseCompletion.
                if req.get("intent") == "course_completion" and req.get("tool") != "CourseCompletion":
                    req["tool"] = "CourseCompletion"
            
            # Merge duplicate requests (if needed) based on request_text.
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

    def update_user_profile(self, state: TutorState) -> Dict:
        """
        Modified to properly handle individual state fields 
        """
        updated_state = state.copy()
        # Update interests
        for request in state.get('multi_requests', []):
            interests = request.get('interests', [])
            for interest in interests:
                if interest and interest not in updated_state["user_profile"]["interests"]:
                    updated_state["user_profile"]["interests"].append(interest)
        
        # Update completed courses
        for request in state.get('multi_requests', []):
            completed_courses = request.get('completed_courses', [])
            for course in completed_courses:
                course_name = course.lower().strip()
                if course_name not in updated_state["completed_courses"]:
                    updated_state["completed_courses"].append(course_name)
        
        # Update current course if specified in the request.
        for request in state.get('multi_requests', []):
            if request.get('current_course'):
                updated_state["current_course"] = request.get('current_course')
                
        # Update current lesson if specified
        for request in state.get('multi_requests', []):
            if request.get('lesson'):
                updated_state["current_lesson"] = request.get('lesson')
        
        return updated_state

    def execute_tools_for_requests(self, state: TutorState) -> Dict:
        updated_state = state.copy()
        requests = state.get('multi_requests', [])
        if not requests:
            logger.warning("No requests to process")
            return {**updated_state, "conversational_response": "I'm not sure what you're asking. Could you clarify your question?"}
        tool_functions = {
            "ExplainConcept": self.explain_concept_for_request,
            "GiveExample": self.give_example_for_request,
            "GenerateQuiz": self.generate_quiz_for_request,
            "SimplifyConcept": self.simplify_concept_for_request,
            "RecommendCourses": self.recommend_courses_for_request,
            "CourseCompletion": self.handle_course_completion_for_request,
            "Fallback": self.fallback_for_request
        }
        agent_responses = {}
        for request in requests:
            request_id = request.get("request_id")
            tool_name = request.get("tool", "Fallback")
            tool_func = tool_functions.get(tool_name, self.fallback_for_request)
            response = tool_func(state, request)
            agent_responses[request_id] = response
        updated_state["agent_responses"] = agent_responses
        return updated_state

    def generate_conversational_response(self, state: TutorState) -> Dict:
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
        print("ASSS" , all_responses)
        print("ASSSsssssssssssssssssssssssss")
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
        response = self.log_and_invoke([{"role": "user", "content": prompt}])
        return {**state, "conversational_response": response.content}

    def log_interaction(self, state: TutorState) -> Dict:
        """
        Modified to properly track interaction metadata for database storage
        """
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
        
        # Update the current state with metadata about this interaction
        updated_state['current_interaction'] = {
            "intent": intent,
            "tool": tool,
            "course": course,
            "lesson": lesson,
            "multi_requests": state.get('multi_requests', [])
        }
        
        # If history is empty, initialize it
        if 'history' not in updated_state:
            updated_state['history'] = []
        
        # Only keep the most recent interaction in memory
        # (The full history is now in the database)
        updated_state['history'] = [{
            "input": state['user_input'],
            "response": state['conversational_response'],
            "intent": intent,
            "tool": tool, 
            "course": course,
            "lesson": lesson
        }]
        
        return updated_state


    # Tool functions
    def explain_concept_for_request(self, state: TutorState, request: Dict) -> str:
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
        
        print("requestttt: ", request_text)
        # Enhance the retrieval query by including course and lesson info
        full_query = f"{course} {lesson} {request_text}"
        context = self.lesson_retriever.invoke(full_query)
        
        print("contexttt: ", context)
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
        response = self.log_and_invoke([{"role": "user", "content": prompt}])
        return response.content


    def give_example_for_request(self, state: TutorState, request: Dict) -> str:
        request_text = request.get("request_text", "")
        if request.get("reference_history", False):
            history_idx = request.get("history_index", -1)
            history = state['history']
            if 0 <= history_idx < len(history):
                referenced_context = history[history_idx].get("input", "")
                request_text = f"{referenced_context} {request_text}"
        context = self.lesson_retriever.invoke(request_text)
        prompt = f"""
        Give a code example for:
        {request_text}
        Context:
        {context}
        Provide a clear, well-commented code example that demonstrates the concept.
        """
        response = self.log_and_invoke([{"role": "user", "content": prompt}])
        return response.content

    def generate_quiz_for_request(self, state: TutorState, request: Dict) -> str:
        request_text = request.get("request_text", "")
        context = self.lesson_retriever.invoke(request_text)
        prompt = f"""
        Create a quiz question for:
        {request_text}
        Context:
        {context}
        Include both the question and the answer.
        """
        response = self.log_and_invoke([{"role": "user", "content": prompt}])
        return response.content

    def simplify_concept_for_request(self, state: TutorState, request: Dict) -> str:
        request_text = request.get("request_text", "")
        prompt = f"Explain like I'm 5: {request_text}"
        response = self.log_and_invoke([{"role": "user", "content": prompt}])
        return response.content

    def recommend_courses_for_request(self, state: TutorState, request: Dict) -> str:
        request_text = request.get("request_text", "")
        completed_courses = state['completed_courses']
        docs = self.course_vectorstore.similarity_search(request_text, k=5) if self.course_vectorstore else []
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
        response = self.log_and_invoke([{"role": "user", "content": prompt}])
        return response.content

    def handle_course_completion_for_request(self, state: TutorState, request: Dict) -> str:
        """
        Modified to better handle course completion
        """
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
        response = self.log_and_invoke([{"role": "user", "content": prompt}])
        
        # No need to update state here as it will be handled in update_user_profile
        # and properly persisted in individual fields
        
        return response.content

    def fallback_for_request(self, state: TutorState, request: Dict) -> str:
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
        response = self.log_and_invoke([{"role": "user", "content": prompt}])
        return response.content

    def invoke(self, state: TutorState) -> Dict:
        results = self.tutor_chain.invoke(state)
        state.update(results)
        return state
