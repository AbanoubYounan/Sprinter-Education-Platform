# student_enrollment_module/progress_services.py
import streamlit as st
from time import sleep
from rich import print  # For pretty rich text output
from uuid import uuid4

def get_instructors(cursor):
    """Fetch all instructors from the users table."""
    cursor.execute("SELECT user_ID, full_name FROM users WHERE role = 'instructor';")
    return cursor.fetchall()

def get_students(cursor): 
    """Fetch all students from the users table."""
    cursor.execute("SELECT user_ID, full_name FROM users WHERE role = 'student';") 
    return cursor.fetchall()

def get_user_enrollments(cursor, user_id):
    """Fetch enrollments, progress, and course ID for a specific user (student or instructor)."""
    query = '''
        SELECT c.course_title, e.status, e.progress, e.course_ID
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



def update_student_progress(cursor, db_conn, student_id, course_title, watched_hours):
    try:
        # Fetch the total hours of the course
        cursor.execute("SELECT total_hours FROM courses WHERE course_title = %s", (course_title,))
        course = cursor.fetchone()

        if not course:
            raise Exception("Course not found.")

        total_hours = course[0]

        if total_hours <= 0:
            raise Exception("Course total hours must be greater than zero.")

        # Calculate progress percentage
        progress_percentage = (watched_hours / total_hours) * 100
        progress_percentage = min(progress_percentage, 100)

        # Insert enrollment with status = 'Active'
        cursor.execute('''
            INSERT INTO enrollments (user_ID, course_ID, progress, status)
            VALUES (
                %s,
                (SELECT course_ID FROM courses WHERE course_title = %s),
                %s,
                'Active'
            )
        ''', (student_id, course_title, progress_percentage))

        db_conn.commit()
        return progress_percentage

    except Exception as e:
        raise Exception(f"Error updating student progress: {e}")



def unenroll_student(cursor, student_id, course_title, db_conn):
    try:
        # First, unenroll the student from the course
        cursor.execute('''
            DELETE FROM enrollments 
            WHERE user_ID = %s AND course_ID = (
                SELECT course_ID FROM courses WHERE course_title = %s
            )
        ''', (student_id, course_title))
        
        # Delete the review if it exists
        cursor.execute('''
            DELETE FROM course_reviews 
            WHERE user_ID = %s AND course_ID = (
                SELECT course_ID FROM courses WHERE course_title = %s
            )
        ''', (student_id, course_title))
        
        db_conn.commit()
        st.success(f"Successfully unenrolled from the course '{course_title}' and review deleted!")
    except Exception as e:
        db_conn.rollback()
        st.error(f"Error while unenrolling from course '{course_title}': {e}")



def add_or_update_review(cursor, db_conn, user_id, course_id, rating, review_text):
    try:
        # Check if the review already exists for the student-course pair
        cursor.execute('''
            SELECT review_ID FROM course_reviews 
            WHERE user_ID = %s AND course_ID = %s
        ''', (user_id, course_id))
        existing_review = cursor.fetchone()

        if existing_review:
            # Update existing review
            cursor.execute('''
                UPDATE course_reviews
                SET rating = %s, review = %s, created_at = CURRENT_TIMESTAMP
                WHERE review_ID = %s
            ''', (rating, review_text, existing_review[0]))
            db_conn.commit()
            st.success("Review updated successfully!")
        else:
            # Insert new review
            review_id = str(uuid4())
            cursor.execute('''
                INSERT INTO course_reviews (review_ID, user_ID, course_ID, rating, review)
                VALUES (%s, %s, %s, %s, %s)
            ''', (review_id, user_id, course_id, rating, review_text))
            db_conn.commit()
            st.success("Review added successfully!")
    except Exception as e:
        db_conn.rollback()
        st.error(f"Error while adding/updating review: {e}")


def get_review_for_course(cursor, user_id, course_id):
    try:
        cursor.execute('''
            SELECT rating, review FROM course_reviews 
            WHERE user_ID = %s AND course_ID = %s
        ''', (user_id, course_id))
        review = cursor.fetchone()

        if review:
            return {"rating": review[0], "review": review[1]}
        else:
            return None
    except Exception as e:
        st.error(f"Error while fetching review: {e}")
        return None

