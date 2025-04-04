from langchain.chat_models import ChatOpenAI
from langchain.agents import Tool
from langchain_community.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import CharacterTextSplitter
import os, re

# ---------------------------------------
# 🔐 API Setup
# ---------------------------------------
os.environ["OPENAI_API_KEY"] = "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"
os.environ["OPENAI_API_BASE"] = "https://api.groq.com/openai/v1"

llm = ChatOpenAI(
    model="llama3-70b-8192",
    temperature=0.5
)

# ---------------------------------------
# 🧠 Embeddings and VectorStores
# ---------------------------------------
embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

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

lesson_text = course_library["web dev with django"]["lessons"]["lesson 2"]
chunks = CharacterTextSplitter(chunk_size=200, chunk_overlap=20).split_text(lesson_text)
lesson_vectorstore = FAISS.from_texts(chunks, embedding)
lesson_retriever = lesson_vectorstore.as_retriever()

courses = [
    {"title": "Intro to Python", "desc": "Beginner-friendly Python course."},
    {"title": "Web Dev with Django", "desc": "Build full-stack web apps with Django."},
    {"title": "Data Science with Pandas", "desc": "Analyze data using Pandas & NumPy."},
    {"title": "Machine Learning Basics", "desc": "Learn ML with Scikit-learn and Python."}
]
course_texts = [f"{c['title']} - {c['desc']}" for c in courses]
course_vectorstore = FAISS.from_texts(course_texts, embedding)

# ---------------------------------------
# 🧾 State Class
# ---------------------------------------
class TutorState:
    def __init__(self):
        self.user_profile = {"name": None, "interests": []}
        self.current_course = ""
        self.current_lesson = ""
        self.history = []
        self.completed_courses = []

    def update_course_context(self, text):
        course_match = re.search(r"(pandas|django|python|machine learning)", text.lower())
        lesson_match = re.search(r"lesson\s*(\d+)", text.lower())

        if course_match:
            course_map = {
                "pandas": "data science with pandas",
                "django": "web dev with django",
                "python": "intro to python",
                "machine learning": "machine learning basics"
            }
            matched = course_match.group(1).lower()
            self.current_course = course_map.get(matched, "")
            if matched in ["pandas"]:
                self.add_interest("data science")
            elif matched in ["django"]:
                self.add_interest("web development")

        if lesson_match:
            self.current_lesson = f"lesson {lesson_match.group(1)}"

    def add_interest(self, topic):
        if topic not in self.user_profile["interests"]:
            self.user_profile["interests"].append(topic)

    def mark_course_completed(self, course_name):
        course_name = course_name.lower().strip()
        if course_name not in self.completed_courses:
            self.completed_courses.append(course_name)

    def log_interaction(self, user_input, intent):
        self.history.append({
            "input": user_input,
            "intent": intent,
            "course": self.current_course,
            "lesson": self.current_lesson
        })


# ---------------------------------------
# INTENT DETECTION
# ---------------------------------------
def detect_intent(query: str):
    q = query.lower()
    if "recommend" in q or "suggest" in q:
        return "recommendation"
    elif "lesson" in q or "i don't understand" in q:
        return "lesson_help"
    elif "example" in q:
        return "example"
    elif "quiz" in q:
        return "quiz"
    elif "simplify" in q:
        return "simplify"
    elif "explain" in q or "what is" in q:
        return "explanation"
    return "fallback"

# ---------------------------------------
# TOOLS WITH STATE ACCESS
# ---------------------------------------
def explain_concept_tool(input_text, state: TutorState):
    context = lesson_retriever.invoke(input_text)
    interests = ", ".join(state.user_profile["interests"]) or "general"
    prompt = f"""
You are a helpful tutor.
Student Interests: {interests}
Course: {state.current_course}
Lesson: {state.current_lesson}
Question: {input_text}

Context:
{context}

Now explain the concept clearly.
"""
    return llm.invoke([{"role": "user", "content": prompt}])

def give_example_tool(input_text, state: TutorState):
    context = lesson_retriever.invoke(input_text)
    prompt = f"Give a code example for:\n{input_text}\n\nContext:\n{context}"
    return llm.invoke([{"role": "user", "content": prompt}])

def generate_quiz_tool(input_text, state: TutorState):
    context = lesson_retriever.invoke(input_text)
    prompt = f"Create a quiz question for:\n{input_text}\n\nContext:\n{context}"
    return llm.invoke([{"role": "user", "content": prompt}])

def simplify_tool(input_text, state: TutorState):
    prompt = f"Explain like I'm 5: {input_text}"
    return llm.invoke([{"role": "user", "content": prompt}])

def recommend_tool(input_text, state: TutorState):
    docs = course_vectorstore.similarity_search(input_text, k=5)

    # Remove completed courses
    filtered = [doc for doc in docs if doc.page_content.split(" - ")[0].lower() not in state.completed_courses]

    if not filtered:
        return "You've already taken all the courses I was going to recommend! 🎉"

    courses = "\n".join([doc.page_content for doc in filtered])
    prompt = f"""The user is interested in: {input_text}
Completed courses: {state.completed_courses}
Here are some available courses:\n{courses}

Recommend one and explain why.
"""
    return llm.invoke([{"role": "user", "content": prompt}])


def fallback_tool(input_text, state: TutorState):
    return "I'm not sure how to help with that yet, but try asking me to explain something or recommend a course!"

# ----------------------------
# ✅ TOOL WRAPPERS with .name
# ----------------------------
class StatefulTool:
    def __init__(self, name, func):
        self.name = name
        self.func = func

# Tools with consistent interface
tools = [
    StatefulTool("ExplainConcept", lambda q: explain_concept_tool(q, state)),
    StatefulTool("GiveExample", lambda q: give_example_tool(q, state)),
    StatefulTool("GenerateQuiz", lambda q: generate_quiz_tool(q, state)),
    StatefulTool("SimplifyConcept", lambda q: simplify_tool(q, state)),
    StatefulTool("RecommendCourses", lambda q: recommend_tool(q, state)),
    StatefulTool("Fallback", lambda q: fallback_tool(q, state))
]

# ----------------------------
# 🧠 Runtime Loop (Clean Style)
# ----------------------------
print("🤖 AI Tutor is ready! Type 'exit' to quit.")
state = TutorState()

while True:
    user_input = input("\nYou: ")
    if user_input.lower() in ["exit", "quit"]:
        print("👋 Goodbye!")
        break

    intent = detect_intent(user_input)
    state.update_course_context(user_input)
    state.log_interaction(user_input, intent)

    intent_map = {
        "lesson_help": "ExplainConcept",
        "explanation": "ExplainConcept",
        "example": "GiveExample",
        "quiz": "GenerateQuiz",
        "simplify": "SimplifyConcept",
        "recommendation": "RecommendCourses",
        "fallback": "Fallback"
    }

    selected_tool_name = intent_map.get(intent, "Fallback")
    selected_tool = next(t for t in tools if t.name == selected_tool_name)
    
    # check for course completion mention
    match = re.search(r"i (already )?(took|completed|finished)\s+(.*)", user_input.lower())
    if match:
        course = match.group(3)
        state.mark_course_completed(course)
        print(f"\n✅ Noted that you completed: {course.title()}")
        continue


    try:
        response = selected_tool.func(user_input)
        print("\n🧠", response.content if hasattr(response, "content") else response)
    except Exception as e:
        print(f"🚨 Error: {e}")
