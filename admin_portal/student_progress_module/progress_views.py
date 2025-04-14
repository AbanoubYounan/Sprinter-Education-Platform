# student_progress_module/progress_views.py

import streamlit as st
from student_progress_module.progress_services import (
    get_instructors,
    get_student_progress
)

def progress_management_view(cursor, db_conn):
    """Displays all students and allows the admin to view their progress."""
    st.title("Student Progress Management")
    students = get_instructors(cursor)

    if students:
        for student in students:
            student_id, student_name = student
            progress_button = st.button(f"👁️ View Progress for {student_name}", key=student_id)

            if progress_button:
                show_student_progress(cursor, student_id)

    else:
        st.warning("No students found in the database.")

def show_student_progress(cursor, student_id):
    """Displays the detailed progress of a specific student."""
    st.subheader(f"Progress for Student ID: {student_id}")
    progress = get_student_progress(cursor, student_id)

    if progress:
        for chapter in progress:
            chapter_id, chapter_title, completed_contents, total_contents = chapter
            completion_percentage = (completed_contents / total_contents) * 100 if total_contents else 0
            st.markdown(f"**{chapter_title}**: {completed_contents}/{total_contents} Completed ({completion_percentage:.2f}%)")
    else:
        st.warning("No progress data available for this student.")
