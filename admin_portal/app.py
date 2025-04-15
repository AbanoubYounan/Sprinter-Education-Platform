import streamlit as st
from db_connection import connect_to_mysql
from user_modules.user_views import user_management_view, edit_user_view, show_user_view, add_user_view
from course_modules.course_views import course_management_view, add_course_view, edit_course_view
from chapter_modules.chapter_views import chapter_management_view, add_chapter_view, edit_chapter_view, view_chapters
from content_modules.content_views import content_management_view, add_content_view, edit_content_view
from student_progress_module.progress_views import progress_management_view
from student_enrollment_module.progress_views import enrollment_management_view
from Course_Progress_Tracker_module.Course_Progress_Tracker_views import course_progress_tracker_view

# ----------------- Connect to DB -----------------
db_conn = connect_to_mysql()
cursor = db_conn.cursor()

# ----------------- Session State Defaults -----------------
if "page_state" not in st.session_state:
    st.session_state.page_state = "home"
if "selected_user_id" not in st.session_state:
    st.session_state.selected_user_id = None

# ----------------- Sidebar Logo & Navigation -----------------
with st.sidebar:
    st.image("assets/sprints_logo.png", width=180)
    st.markdown("## 🛠️ Admin Panel", unsafe_allow_html=True)
    page = st.radio("📚 **Navigate to Module**", [
        "👤 Users",
        "📘 Courses",
        "📂 Chapters",
        "📝 Enrollment",
        "📊 Course Progress Tracker",
        "📈 Dashboard"
    ])
    st.markdown("---")
    st.caption("Developed with ❤️ by Sprints Team 1")

# ----------------- Main Views -----------------
if st.session_state.page_state == "home":
    if page == "👤 Users":
        user_management_view(cursor, db_conn)
    elif page == "📘 Courses":
        course_management_view(cursor, db_conn)
    elif page == "📂 Chapters":
        chapter_management_view(cursor, db_conn)
    elif page == "📝 Enrollment":
        enrollment_management_view(cursor, db_conn)
    elif page == "📊 Course Progress Tracker":
        course_progress_tracker_view(cursor, db_conn)
    elif page == "📈 Dashboard":
        progress_management_view(cursor, db_conn)

# ----------------- User Pages -----------------
elif st.session_state.page_state == "edit_user":
    if st.session_state.selected_user_id:
        edit_user_view(cursor, db_conn, st.session_state.selected_user_id)
    else:
        st.error("⚠️ No user selected for editing.")

elif st.session_state.page_state == "show_user":
    if st.session_state.selected_user_id:
        show_user_view(cursor, db_conn, st.session_state.selected_user_id)
    else:
        st.error("⚠️ No user selected to display.")

elif st.session_state.page_state == "add_user":
    add_user_view(cursor, db_conn)

# ----------------- Course Pages -----------------
elif st.session_state.page_state == "add_course":
    add_course_view(cursor, db_conn)

elif st.session_state.page_state == "edit_course":
    course_id = st.session_state.get('selected_course_id', None)
    if course_id:
        edit_course_view(cursor, db_conn, course_id)
    else:
        st.error("⚠️ No course selected for editing.")

# ----------------- Chapter Pages -----------------
elif st.session_state.page_state == "add_chapter":
    add_chapter_view(cursor, db_conn)

elif st.session_state.page_state == "view_chapters":
    view_chapters(cursor, db_conn)

elif st.session_state.page_state == "edit_chapter":
    edit_chapter_view(cursor, db_conn, st.session_state.selected_chapter_id)

# ----------------- Content Pages -----------------
elif st.session_state.page_state == "view_content":
    content_management_view(cursor, db_conn)

elif st.session_state.page_state == "add_content":
    add_content_view(cursor, db_conn)

elif st.session_state.page_state == "edit_content":
    edit_content_view(cursor, db_conn)
