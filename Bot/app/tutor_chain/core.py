import os
from langchain.chat_models import ChatOpenAI
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv
from helpers.course_names import get_course_titles
from app.tutor_chain.config import logger, TutorState
from app.tutor_chain.chain_steps import (
    analyze_input_with_llm,
    update_user_profile,
    execute_tools_for_requests,
    generate_conversational_response,
    log_interaction,
    build_context_node
)
from app.tutor_chain.tool_functions import (
    explain_concept_for_request,
    give_example_for_request,
    generate_quiz_for_request,
    simplify_concept_for_request,
    recommend_courses_for_request,
    handle_course_completion_for_request,
    fallback_for_request,
    converse_for_request,
    pdf_search_for_request
)
from helpers.courses_details import get_courses

load_dotenv()


class TutorChain:
    def __init__(self):
        os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
        os.environ["GROQ_API_KEY"] = os.getenv("OPENAI_API_KEY")
        os.environ["OPENAI_API_BASE"] = os.getenv("OPENAI_API_BASE")
        self.llm = ChatOpenAI(
            model="llama3-70b-8192",
            temperature=0.5,
            max_tokens=400
        )
        self.embedding = self.get_embedding_model()
        
        # Unified dictionary combining courses and lessons.
        self.unified_courses = get_courses()
        
        self.course_names = get_course_titles()
        # Initialize one unified vector store using the unified dictionary.
        self.init_vectorstores()
        
        self.workflow = StateGraph(TutorState)
        self.workflow.add_node("analyze_input", lambda state: analyze_input_with_llm(self, state))
        self.workflow.add_node("update_profile", lambda state: update_user_profile(self, state))
        self.workflow.add_node("build_context", lambda state: build_context_node(self, state))
        self.workflow.add_node("execute_tools", lambda state: execute_tools_for_requests(self, state))
        self.workflow.add_node("generate_response", lambda state: generate_conversational_response(self, state))
        self.workflow.add_node("log_interaction", lambda state: log_interaction(self, state))

        self.workflow.add_edge("analyze_input", "update_profile")
        self.workflow.add_edge("update_profile", "build_context")
        self.workflow.add_edge("build_context", "execute_tools")
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
        self.converse_for_request = converse_for_request
        self.pdf_search_for_request = pdf_search_for_request

    def should_continue(self, state: TutorState) -> str:
        if state.get('should_exit', False):
            logger.info("Chain exiting based on should_exit flag")
            return "end"
        return "continue"

    def get_embedding_model(self):
        try:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
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
        # Build documents from the unified courses.
        documents = []
        for course_name, course_data in self.unified_courses.items():
            doc = f"Course: {course_name}\nDescription: {course_data['course_disc']}\n"
            if course_data["lessons"]:
                doc += "Lessons:\n"
                for lesson_id, lesson in course_data["lessons"].items():
                    doc += (
                        f"{lesson_id}: Title: {lesson['lesson_title']} - Description: {lesson['lesson_disc']}\n"
                    )
            documents.append(doc)
        
        try:
            self.vectorstore = FAISS.from_texts(documents, self.embedding)
            self.vector_retriever = self.vectorstore.as_retriever()
        except Exception as e:
            logger.error(f"Failed to create vectorstore: {e}")
            def simple_retriever(query):
                query = query.lower()
                matches = [doc for doc in documents if any(word in doc.lower() for word in query.split())]
                return matches[0] if matches else "No specific context available."
            self.vector_retriever = lambda q: simple_retriever(q)

    def log_and_invoke(self, messages, tool_name="Unknown", **kwargs):
        # Log the tool being executed along with the prompt messages.
        logger.info("Executing tool: %s", tool_name)
        # logger.debug("Prompt for %s: %s", tool_name, messages)
        
        response = self.llm.invoke(messages, **kwargs)
        
        # Log the response content and the order in which tools are executed.
        logger.info("Completed tool: %s", tool_name)
        logger.debug("Response from %s: %s", tool_name, response.content)
        # print("done!")
        
        return response


    def invoke(self, state: TutorState) -> dict:
        # logger.info("INVOKINGGGGG")
        # logger.info(state)
        results = self.tutor_chain.invoke(state)
        state.update(results)
        return state
