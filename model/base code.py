from langchain.chat_models import ChatOpenAI
from langchain.agents import Tool
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import CharacterTextSplitter
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
import os, json

# API keys setup
os.environ["OPENAI_API_KEY"] = "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"
os.environ["OPENAI_API_BASE"] = "https://api.groq.com/openai/v1"

# Setup LLM
llm = ChatOpenAI(
    model="llama3-70b-8192",
    temperature=0.5
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

class TutorState:
    def __init__(self):
        self.user_profile = {"name": None, "interests": []}
        self.current_course = ""
        self.current_lesson = ""
        self.history = []
        self.completed_courses = []

    def analyze_input_with_llm(self, text):
        """Use LLM to analyze user input and determine context, interests, and intent"""
        course_options = ["intro to python", "web dev with django", "data science with pandas", "machine learning basics"]
        interest_options = ["programming", "web development", "data science", "machine learning", "artificial intelligence", "python"]
        intent_options = [
            "explanation - user wants a concept explained",
            "example - user wants an example",
            "quiz - user wants to be quizzed",
            "simplify - user wants a simpler explanation",
            "recommendation - user wants course recommendations",
            "course_completion - user is indicating they've completed course(s)",
            "fallback - intent is unclear"
        ]
        # Include chat history in the prompt for context
        chat_history = "\n".join([f"You: {h['input']} | AI: {h['response']}" for h in self.history[-5:]])
        prompt = f"""
        Given the user's message and recent chat history, analyze the following:
        1. What course they might be referring to (if any)
        2. What lesson number they might be referring to (if any)
        3. What interests they might have based on their message
        4. What courses they have completed (if they indicate any)
        5. What is their primary intent/need
        Available courses: {course_options}
        Common interests: {interest_options}
        Possible intents: {intent_options}
        Recent Chat History:
        {chat_history}
        User message: "{text}"
        Return your analysis STRICTLY as a JSON object with these fields:
        {{
            "course": "course name or empty string",
            "lesson": "lesson number or empty string",
            "interests": ["list", "of", "interests"],
            "completed_courses": ["list", "of", "completed", "courses"],
            "intent": "one of the intent options",
            "tool": "ExplainConcept/GiveExample/GenerateQuiz/SimplifyConcept/RecommendCourses/CourseCompletion/Fallback"
        }}
        Make sure the response is valid JSON and nothing else.
        """
        response = llm.invoke([{"role": "user", "content": prompt}])
        try:
            result = json.loads(response.content)
            return result
        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            return {
                "course": "",
                "lesson": "",
                "interests": [],
                "completed_courses": [],
                "intent": "fallback",
                "tool": "Fallback"
            }

    def update_from_analysis(self, analysis):
        """Update the TutorState based on the analysis from the LLM"""
        # Update current course
        if analysis.get("course"):
            self.current_course = analysis["course"].lower()

        # Update current lesson
        if analysis.get("lesson"):
            lesson_num = analysis["lesson"]
            if not lesson_num.lower().startswith("lesson"):
                lesson_num = f"lesson {lesson_num}"
            self.current_lesson = lesson_num

        # Add new interests
        for interest in analysis.get("interests", []):
            self.add_interest(interest.lower())

        # Mark courses as completed
        for course in analysis.get("completed_courses", []):
            self.mark_course_completed(course.lower())

    def add_interest(self, topic):
        """Add a new interest to the user profile if it's not already present"""
        if topic and topic not in self.user_profile["interests"]:
            self.user_profile["interests"].append(topic)

    def mark_course_completed(self, course_name):
        """Mark a course as completed if it's not already marked"""
        course_name = course_name.lower().strip()
        if course_name not in self.completed_courses:
            self.completed_courses.append(course_name)

    def log_interaction(self, user_input, ai_response, intent, tool):
        """Log both user input and AI response for future reference"""
        self.history.append({
            "input": user_input,
            "response": ai_response,  # Include the AI's response
            "intent": intent,
            "tool": tool,
            "course": self.current_course,
            "lesson": self.current_lesson
        })
                
            
# Define tools using the new LCEL syntax
explain_concept_chain = (
    RunnablePassthrough.assign(context=lambda x: lesson_retriever.invoke(x["input_text"])) 
    | PromptTemplate.from_template("""
You are a helpful tutor.
Student Interests: {interests}
Course: {current_course}
Lesson: {current_lesson}
Question: {input_text}
Context:
{context}
Now explain the concept clearly.
""")
    | llm
    | StrOutputParser()
)

give_example_chain = (
    RunnablePassthrough.assign(context=lambda x: lesson_retriever.invoke(x["input_text"]))
    | PromptTemplate.from_template("""
Give a code example for:
{input_text}
Context:
{context}
""")
    | llm
    | StrOutputParser()
)

generate_quiz_chain = (
    RunnablePassthrough.assign(context=lambda x: lesson_retriever.invoke(x["input_text"]))
    | PromptTemplate.from_template("""
Create a quiz question for:
{input_text}
Context:
{context}
""")
    | llm
    | StrOutputParser()
)

simplify_chain = (
    PromptTemplate.from_template("Explain like I'm 5: {input_text}")
    | llm
    | StrOutputParser()
)

# Fixed recommend_chain to keep the output as a dictionary instead of converting to list
def process_course_recommendations(x):
    # Get documents from vectorstore
    docs = course_vectorstore.similarity_search(x["input_text"], k=5)
    # Filter out completed courses
    available_courses = []
    for doc in docs:
        course_title = doc.page_content.split(" - ")[0].lower()
        if course_title not in x["completed_courses"]:
            available_courses.append(doc.page_content)
    # Return as a dictionary with the available courses
    return {"docs": "\n".join(available_courses), "input_text": x["input_text"], "completed_courses": x["completed_courses"]}

recommend_chain = (
    RunnableLambda(process_course_recommendations)
    | PromptTemplate.from_template("""
The user is interested in: {input_text}
Completed courses: {completed_courses}
Available courses:
{docs}
Recommend one and explain why.
""")
    | llm
    | StrOutputParser()

)

handle_course_completion_chain = (
    PromptTemplate.from_template("""
The user has indicated they've completed some courses.
Available courses: ["intro to python", "web dev with django", "data science with pandas", "machine learning basics"]
User's message: "{input_text}"
Courses that user want to mark as completed: "{user_courses}"
Extract the exact names of the completed courses from the user's message.
Return ONLY a JSON list of completed courses (e.g., ["intro to python"]).
If no specific courses are mentioned, return an empty list ([]).
""")
    | llm
    | StrOutputParser()
)

fallback_chain = (
    PromptTemplate.from_template("I'm not sure how to help with that. Try asking me to explain something or recommend a course!")
    | llm
    | StrOutputParser()
)

# Initialize state and vectorstores
print("🤖 AI Tutor is ready! Type 'exit' to quit.")
init_vectorstores()
state = TutorState()

while True:
    user_input = input("\nYou: ")
    if user_input.lower() in ["exit", "quit"]:
        print("👋 Goodbye!")
        break

    # Analyze input and determine intent, context, and appropriate tool
    analysis = state.analyze_input_with_llm(user_input)
    state.update_from_analysis(analysis)

    # Select and use the appropriate tool based on LLM analysis
    selected_tool_name = analysis.get("tool", "Fallback")
    if selected_tool_name == "ExplainConcept":
        agent_response = explain_concept_chain.invoke({
            "input_text": user_input,
            "interests": ", ".join(state.user_profile["interests"]),
            "current_course": state.current_course,
            "current_lesson": state.current_lesson
        })
    elif selected_tool_name == "GiveExample":
        agent_response = give_example_chain.invoke({
            "input_text": user_input
        })
    elif selected_tool_name == "GenerateQuiz":
        agent_response = generate_quiz_chain.invoke({
            "input_text": user_input
        })
    elif selected_tool_name == "SimplifyConcept":
        agent_response = simplify_chain.invoke({
            "input_text": user_input
        })
    elif selected_tool_name == "RecommendCourses":
        agent_response = recommend_chain.invoke({
            "input_text": user_input,
            "completed_courses": state.completed_courses
        })
    elif selected_tool_name == "CourseCompletion":
        agent_response = handle_course_completion_chain.invoke({
            "input_text": user_input,
            "user_courses": analysis["completed_courses"]
        })
    else:
        agent_response = fallback_chain.invoke({})

    # Log the intermediate response from the first LLM
    state.log_interaction(user_input, agent_response, analysis.get("intent", "fallback"), analysis.get("tool", "Fallback"))

    # Generate a conversational response using the second LLM
    conversational_response = (
        PromptTemplate.from_template("""
You are a conversational AI tutor. Based on the following information, craft a natural, conversational response to the user you should answer the user question and asses him in his request if you found his request already fulfilled just continue with the flow if not you should fulfill it dont ask the user what should you do IF YOU FOUND HIS REQUEST NOT FULFILLED AND FINISHED MAKE SURE YOU ASSES HIM:
- User Input: "{user_input}"
- Agent Response: "{agent_response}"
- User Profile: {user_profile}
- Completed Courses: {completed_courses}
- Current Course: {current_course}
- Current Lesson: {current_lesson}
- Recent Chat History:
{chat_history}
""")
        | llm
        | StrOutputParser()
    ).invoke({
        "user_input": user_input,
        "agent_response": agent_response,
        "user_profile": json.dumps(state.user_profile),
        "completed_courses": ", ".join(state.completed_courses),
        "current_course": state.current_course,
        "current_lesson": state.current_lesson,
        "chat_history": "\n".join([f"You: {h['input']} | AI: {h['response']}" for h in state.history[-5:]])
    })

    # Log the final conversational response
    state.log_interaction(user_input, conversational_response, analysis.get("intent", "fallback"), "ConversationalLLM")

    # Display the final response to the user
    print("\n🧠", conversational_response)