import mysql.connector
import streamlit as st
from rich.console import Console
console = Console()

# Function to fetch the enrollments and progress for a specific user
def get_user_enrollments(cursor, user_id):
    """
    Fetch enrollments and progress for a specific user (student or instructor).
    """
    query = '''
        SELECT c.course_ID, c.course_title, e.status, e.progress
        FROM enrollments e
        JOIN courses c ON e.course_ID = c.course_ID
        WHERE e.user_ID = %s
    '''
    cursor.execute(query, (user_id,))
    return cursor.fetchall()

# Function to fetch the chapters of a specific course
def get_chapters_for_course(cursor, course_id):
    """
    Fetch chapter details (including position) for the selected course.
    """
    cursor.execute("""
        SELECT c.chapter_ID, c.title, c.description, cc.position 
        FROM chapters c
        JOIN course_chapters cc ON c.chapter_ID = cc.chapter_ID
        WHERE cc.course_ID = %s
        ORDER BY cc.position
    """, (course_id,))
    return cursor.fetchall()

# Function to fetch the student's progress for a specific chapter
def get_student_progress(cursor, student_id, chapter_id):
    """
    Get content of a chapter and whether it is completed by the student.
    """
    cursor.execute("""
        SELECT c.content_ID, c.content_title,
            CASE WHEN sp.content_ID IS NOT NULL THEN 1 ELSE 0 END AS completed
        FROM chapter_content cc
        JOIN content c ON cc.content_ID = c.content_ID
        LEFT JOIN student_progress sp
            ON c.content_ID = sp.content_ID AND sp.user_ID = %s AND sp.chapter_ID = %s
        WHERE cc.chapter_ID = %s
        ORDER BY cc.position
    """, (student_id, chapter_id, chapter_id))
    return cursor.fetchall()


# Function to update student's progress in a specific chapter
def update_student_progress(cursor, db_conn, student_id, content_id, watched, course_id, chapter_id):
    # Check if there's already a progress record
    cursor.execute("""
        SELECT completed FROM student_progress
        WHERE user_ID = %s AND content_ID = %s
    """, (student_id, content_id))
    result = cursor.fetchone()

    # Attempt to get content and chapter title for better message
    try:
        cursor.execute("SELECT content_title FROM content WHERE content_ID = %s", (content_id,))
        content_title = cursor.fetchone()[0]
    except:
        content_title = f"Content {content_id}"

    try:
        cursor.execute("SELECT title FROM chapters WHERE chapter_ID = %s", (chapter_id,))
        chapter_title = cursor.fetchone()[0]
    except:
        chapter_title = f"Chapter {chapter_id}"

    # Update or Insert progress record
    if result:
        # Update existing record
        cursor.execute("""
            UPDATE student_progress
            SET completed = %s
            WHERE user_ID = %s AND content_ID = %s
        """, (watched, student_id, content_id))
    else:
        # Insert new progress record
        cursor.execute("""
            INSERT INTO student_progress (user_ID, course_ID, chapter_ID, content_ID, completed)
            VALUES (%s, %s, %s, %s, %s)
        """, (student_id, course_id, chapter_id, content_id, watched))

    # Update the course progress
    cursor.execute("""
        SELECT progress FROM enrollments WHERE user_ID = %s AND course_ID = %s
    """, (student_id, course_id))
    current_progress = cursor.fetchone()[0]

    # Get the total hours for the course directly from the courses table
    cursor.execute("""
        SELECT total_hours FROM courses WHERE course_ID = %s
    """, (course_id,))
    total_course_hours = cursor.fetchone()[0] or 0

    # Calculate the total hours of completed content
    cursor.execute("""
        SELECT SUM(c.duration) 
        FROM student_progress sp
        JOIN chapter_content cc ON sp.content_ID = cc.content_ID
        JOIN course_chapters cch ON cc.chapter_ID = cch.chapter_ID
        JOIN content c ON sp.content_ID = c.content_ID
        WHERE sp.user_ID = %s AND cch.course_ID = %s AND sp.completed = TRUE
    """, (student_id, course_id))
    completed_course_hours = cursor.fetchone()[0] or 0

    # Calculate the new progress as the ratio of completed hours to total course hours
    new_progress = (completed_course_hours /(total_course_hours*60)) * 100 if total_course_hours > 0 else 0

    # Update the progress in the enrollments table
    cursor.execute("""
        UPDATE enrollments
        SET progress = %s
        WHERE user_ID = %s AND course_ID = %s
    """, (new_progress, student_id, course_id))

    # If progress is 100%, update status to 'Completed'
    if new_progress >= 100:
        cursor.execute("""
            UPDATE enrollments
            SET status = 'Completed'
            WHERE user_ID = %s AND course_ID = %s
        """, (student_id, course_id))
    else:
        cursor.execute("""
            UPDATE enrollments
            SET status = 'Active'
            WHERE user_ID = %s AND course_ID = %s
        """, (student_id, course_id))

    db_conn.commit()

    status = "✅ Watched" if watched else "❌ Unwatched"
    return f"🔄 Updated progress for **{content_title}** in _{chapter_title}_ → {status}. Progress updated from {current_progress:.2f}% to {new_progress:.2f}%"










def get_student_progress(cursor, student_id, content_id):
    cursor.execute("""
        SELECT completed FROM student_progress
        WHERE user_ID = %s AND content_ID = %s
    """, (student_id, content_id))
    result = cursor.fetchone()
    return result[0] if result else False

