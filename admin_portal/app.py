import streamlit as st
from db_connection import connect_to_mysql
from user_modules.user_views import user_management_view, edit_user_view, show_user_view, add_user_view
from course_modules.course_views import course_management_view, add_course_view, edit_course_view
from chapter_modules.chapter_views import chapter_management_view, add_chapter_view, edit_chapter_view, view_chapters
from content_modules.content_views import content_management_view, add_content_view, edit_content_view
from student_progress_module.progress_views import progress_management_view
from student_enrollment_module.progress_views import enrollment_management_view
from Course_Progress_Tracker_module.Course_Progress_Tracker_views import course_progress_tracker_view

# Connect to the database
db_conn = connect_to_mysql()
cursor = db_conn.cursor()

# Page state management
if "page_state" not in st.session_state:
    st.session_state.page_state = "home"  # Default state is home
if "selected_user_id" not in st.session_state:
    st.session_state.selected_user_id = None  # No user selected initially

# Render based on state
if st.session_state.page_state == "home":
    st.sidebar.title("🎓 Admin Panel")
    page = st.sidebar.radio("📁 Select Module", ["Users", "Courses", "Chapters","enrollment","Course Progress Tracker","dashboard"])  # Allow selection between Users, Courses, Chapters
    if page == "Users":
        user_management_view(cursor, db_conn)  # Function for managing users
    elif page== "Courses":
        course_management_view(cursor, db_conn) # Function for managing courses
    elif page=="Chapters":
        chapter_management_view(cursor,db_conn) # Function for managing chapters
    elif page=="enrollment":
        enrollment_management_view(cursor,db_conn) # Function for managing chapters
    elif page=="Course Progress Tracker":
        course_progress_tracker_view(cursor,db_conn) # Function to simulate watching
    elif page=="dashboard":
        progress_management_view(cursor,db_conn) # Function for managing progress


##################################################  User Pages #########################################################

# Edit User
elif st.session_state.page_state == "edit_user":
    if st.session_state.selected_user_id:
        edit_user_view(cursor, db_conn, st.session_state.selected_user_id)  # Function to edit user data
    else:
        st.error("No user selected for editing.")

# Show User
elif st.session_state.page_state == "show_user":
    if st.session_state.selected_user_id:
        show_user_view(cursor, db_conn, st.session_state.selected_user_id)  # Function to show user details
    else:
        st.error("No user selected to display.")

# Add User
elif st.session_state.page_state == "add_user":
    add_user_view(cursor, db_conn)  # Function to add a new user

##################################################  User Pages #########################################################

# Add_Course
elif st.session_state.page_state == "add_course":
    add_course_view(cursor, db_conn)  # Function to add a new course

# Edit_Course
elif st.session_state.page_state == "edit_course":
    # Ensure that the course_id is available in the session state
    course_id = st.session_state.get('selected_course_id', None)
    
    # Check if the course_id is available and valid
    if course_id:
        # Call the edit_course_view function with cursor, db_conn, and the course_id
        edit_course_view(cursor, db_conn, course_id)
    else:
        st.error("No course selected for editing.")


##################################################  Courses Pages #########################################################
elif st.session_state.page_state == "add_course":
    add_course_view(cursor, db_conn)  # Function to add a new course


##################################################  Chapters Pages #########################################################

elif st.session_state.page_state == "add_chapter":
    add_chapter_view(cursor, db_conn)  # Function to add a new chapter

elif st.session_state.page_state == "view_chapters":
    view_chapters(cursor, db_conn)  # Function to view chapters

elif st.session_state.page_state == "edit_chapter":
    edit_chapter_view(cursor, db_conn, st.session_state.selected_chapter_id)  # Edit chapter view


##################################################  Content Pages #########################################################
elif st.session_state.get("page_state") == "view_content":
    content_management_view(cursor, db_conn)

elif st.session_state.get("page_state") == "add_content":
    add_content_view(cursor, db_conn)
    
elif st.session_state.get("page_state") == "edit_content":
    edit_content_view(cursor, db_conn)

##################################################  Content Pages #########################################################

