# student_enrollment_module/progress_services.py
import streamlit as st
from time import sleep
from rich import print  # For pretty rich text output

def get_instructors(cursor):
    """Fetch all instructors from the users table."""
    cursor.execute("SELECT user_ID, full_name FROM users WHERE role = 'instructor';")
    return cursor.fetchall()

def get_students(cursor): 
    """Fetch all students from the users table."""
    cursor.execute("SELECT user_ID, full_name FROM users WHERE role = 'student';") 
    return cursor.fetchall()

def get_user_enrollments(cursor, user_id):
    """Fetch enrollments and progress for a specific user (student or instructor)."""
    query = '''
        SELECT c.course_title, e.status, e.progress
        FROM enrollments e
        JOIN courses c ON e.course_ID = c.course_ID
        WHERE e.user_ID = %s
    '''
    cursor.execute(query, (user_id,))
    return cursor.fetchall()



def get_instructor_courses(cursor, instructor_id):
    """Fetch all courses created by a given instructor."""
    cursor.execute("""
        SELECT course_title, course_ID, category, level, price, total_hours
        FROM courses
        WHERE instructor_id = %s
    """, (instructor_id,))
    return cursor.fetchall()

def get_courses(cursor):
    """Fetch all available courses with their IDs and titles."""
    cursor.execute("SELECT course_ID, course_title FROM courses")
    return cursor.fetchall()



def display_student_enrollments(cursor):
    st.subheader("All Students and Their Enrollments")

    students = get_students(cursor)

    if not students:
        st.info("No students found.")
    else:
        for student_id, full_name in students:
            with st.expander(f"👤 {full_name}", expanded=True):
                # Add a cool animation effect
                st.markdown(f"<h4 style='color: #4CAF50;'>Enrollments:</h4>", unsafe_allow_html=True)

                # Fetching enrollments for the student
                enrollments = get_user_enrollments(cursor, student_id)
                if enrollments:
                    for title, status, progress in enrollments:
                        # Dynamic coloring based on progress
                        progress_percentage = int(progress)
                        if progress_percentage == 100:
                            status_color = "green"
                        elif progress_percentage >= 75:
                            status_color = "yellow"
                        else:
                            status_color = "red"
                        
                        # Animation with "Status: "
                        st.markdown(f"<p style='font-size:18px; color:{status_color};'>📘 **{title}**</p>", unsafe_allow_html=True)
                        st.write(f"   ➡️ Status: {status}, Progress: {progress}%")
                        sleep(0.5)  # Delay for animation effect
                else:
                    st.write("No enrollments.")

def simulate_watching_content(cursor):
    # Tab for simulating course watching and progress update
    with st.container():
        st.subheader("Simulate Student Watching Content and Update Progress")

        # Step 1: Choose the student from a dropdown
        students = get_students(cursor)
        student_options = [full_name for _, full_name in students]
        selected_student = st.selectbox("Select Student", student_options)

        # Step 2: Fetch student ID based on selected name
        selected_student_id = [student_id for student_id, full_name in students if full_name == selected_student][0]

        # Step 3: Show all courses the student is enrolled in
        enrollments = get_student_enrollments(cursor, selected_student_id)
        if not enrollments:
            st.write("This student is not enrolled in any courses.")
        else:
            # Show the courses in a selectbox
            course_titles = [title for title, _, _ in enrollments]
            selected_course = st.selectbox("Select Course", course_titles)

            # Get selected course details
            selected_course_details = next((title, status, progress, total_hours) for title, status, progress, total_hours in enrollments if title == selected_course)

            # Show course progress
            course_title, status, progress, total_hours = selected_course_details
            st.write(f"Course: {course_title}")
            st.write(f"Current Progress: {progress}%")
            st.write(f"Total Hours: {total_hours} hours")

            # Step 4: Simulate "Watch" button to increase progress
            watched_hours = st.slider("Watched Hours", min_value=0, max_value=total_hours, value=0, step=1)

            if st.button("Update Progress"):
                if watched_hours > 0:
                    # Calculate new progress
                    new_progress = (watched_hours / total_hours) * 100
                    new_progress = min(new_progress, 100)  # Ensure progress doesn't go over 100%

                    # Update progress in the database (assuming there is a function for that)
                    update_student_progress(cursor, selected_student_id, selected_course, new_progress)

                    st.success(f"Progress updated to {new_progress:.2f}%")
                else:
                    st.warning("Please select watched hours.")

def update_student_progress(cursor, student_id, course_title, watched_hours):
    try:
        # Fetch the total hours of the course
        cursor.execute("SELECT total_hours FROM courses WHERE course_title = %s", (course_title,))
        course = cursor.fetchone()

        if not course:
            raise Exception("Course not found.")

        total_hours = course[0]

        if total_hours <= 0:
            raise Exception("Course total hours must be greater than zero.")

        # Calculate the progress percentage
        progress_percentage = (watched_hours / total_hours) * 100
        progress_percentage = min(progress_percentage, 100)  # Ensure it doesn't exceed 100%

        # Update the progress in the enrollments table
        cursor.execute('''
            UPDATE enrollments
            SET progress = %s
            WHERE user_ID = %s AND course_ID = (SELECT course_ID FROM courses WHERE course_title = %s)
        ''', (progress_percentage, student_id, course_title))

        cursor.connection.commit()

        return progress_percentage  # Return the calculated progress for confirmation
    except Exception as e:
        raise Exception(f"Error updating student progress: {e}")
