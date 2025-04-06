import os
from langchain.chat_models import ChatOpenAI
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langgraph.graph import StateGraph, END

from app.tutor_chain.config import logger, TutorState
from app.tutor_chain.chain_steps import (
    analyze_input_with_llm,
    update_user_profile,
    execute_tools_for_requests,
    generate_conversational_response,
    log_interaction
)
from app.tutor_chain.tool_functions import (
    explain_concept_for_request,
    give_example_for_request,
    generate_quiz_for_request,
    simplify_concept_for_request,
    recommend_courses_for_request,
    handle_course_completion_for_request,
    fallback_for_request
)

class TutorChain:
    def __init__(self):
        os.environ["OPENAI_API_KEY"] = "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"
        os.environ["OPENAI_API_BASE"] = "https://api.groq.com/openai/v1"
        self.llm = ChatOpenAI(
            model="llama3-70b-8192",
            temperature=0.5,
            max_tokens=400
        )
        self.embedding = self.get_embedding_model()
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
        self.lesson_vectorstore = None
        self.lesson_retriever = None
        self.course_vectorstore = None
        self.init_vectorstores()
        self.workflow = StateGraph(TutorState)
        # Assign chain step functions (wrapped to pass self)
        self.workflow.add_node("analyze_input", lambda state: analyze_input_with_llm(self, state))
        self.workflow.add_node("update_profile", lambda state: update_user_profile(self, state))
        self.workflow.add_node("execute_tools", lambda state: execute_tools_for_requests(self, state))
        self.workflow.add_node("generate_response", lambda state: generate_conversational_response(self, state))
        self.workflow.add_node("log_interaction", lambda state: log_interaction(self, state))
        self.workflow.add_edge("analyze_input", "update_profile")
        self.workflow.add_edge("update_profile", "execute_tools")
        self.workflow.add_edge("execute_tools", "generate_response")
        self.workflow.add_edge("generate_response", "log_interaction")
        self.workflow.add_edge("log_interaction", END)
        self.workflow.add_conditional_edges("analyze_input", self.should_continue, {"continue": "update_profile", "end": END})
        self.workflow.set_entry_point("analyze_input")
        self.tutor_chain = self.workflow.compile()
        # Bind tool functions to instance
        self.explain_concept_for_request = explain_concept_for_request
        self.give_example_for_request = give_example_for_request
        self.generate_quiz_for_request = generate_quiz_for_request
        self.simplify_concept_for_request = simplify_concept_for_request
        self.recommend_courses_for_request = recommend_courses_for_request
        self.handle_course_completion_for_request = handle_course_completion_for_request
        self.fallback_for_request = fallback_for_request

    def should_continue(self, state: TutorState) -> str:
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

    def invoke(self, state: TutorState) -> dict:
        results = self.tutor_chain.invoke(state)
        state.update(results)
        return state
