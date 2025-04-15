# File: student_progress_module/progress_services.py
import datetime
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px

def fetch_student_progress(cursor):
    query = '''
        SELECT u.user_ID, u.full_name, c.course_ID, c.course_title, e.progress
        FROM enrollments e
        JOIN users u ON u.user_ID = e.user_ID
        JOIN courses c ON c.course_ID = e.course_ID
        WHERE u.role = 'student'
    '''
    cursor.execute(query)
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    return pd.DataFrame(rows, columns=columns)


def fetch_top_students(cursor, limit=10):
    query = '''
        SELECT u.user_ID, u.full_name, COUNT(e.course_ID) AS enrolled_courses
        FROM enrollments e
        JOIN users u ON u.user_ID = e.user_ID
        WHERE u.role = 'student'
        GROUP BY u.user_ID, u.full_name
        ORDER BY enrolled_courses DESC
        LIMIT %s
    '''
    cursor.execute(query, (limit,))
    return cursor.fetchall()


def fetch_top_instructors(cursor, limit=10):
    query = '''
        SELECT u.user_ID, u.full_name, COUNT(c.course_ID) AS published_courses
        FROM courses c
        JOIN users u ON u.user_ID = c.instructor_ID
        WHERE u.role = 'instructor'
        GROUP BY u.user_ID, u.full_name
        ORDER BY published_courses DESC
        LIMIT %s
    '''
    cursor.execute(query, (limit,))
    return cursor.fetchall()

# def get_student_progress_data(cursor, student_id, chapter_id):
#     """
#     Get content of a chapter and whether it is completed by the student.
#     """
#     cursor.execute("""
#         SELECT c.content_ID, c.content_title,
#             CASE WHEN sp.content_ID IS NOT NULL THEN 1 ELSE 0 END AS completed
#         FROM chapter_content cc
#         JOIN content c ON cc.content_ID = c.content_ID
#         LEFT JOIN student_progress sp
#             ON c.content_ID = sp.content_ID AND sp.user_ID = %s AND sp.chapter_ID = %s
#         WHERE cc.chapter_ID = %s
#         ORDER BY cc.position
#     """, (student_id, chapter_id, chapter_id))
#     return cursor.fetchall()

def get_total_counts(cursor):
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'student'")
    total_students = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'instructor'")
    total_instructors = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM courses")
    total_courses = cursor.fetchone()[0]

    return total_students, total_instructors, total_courses

def get_top_students_by_enrollments(cursor):
    cursor.execute("""
        SELECT u.full_name AS student_name, COUNT(e.course_id) AS enrolled_courses
        FROM enrollments e
        JOIN users u ON e.user_id = u.user_id
        WHERE u.role = 'student'
        GROUP BY u.full_name
        ORDER BY enrolled_courses DESC
        LIMIT 10
    """)
    result = cursor.fetchall()
    return pd.DataFrame(result, columns=["Student Name", "Enrolled Courses"])

def get_top_instructors_by_courses(cursor):
    cursor.execute("""
        SELECT u.full_name AS instructor_name, COUNT(c.course_id) AS course_count
        FROM courses c
        JOIN users u ON c.instructor_id = u.user_id
        WHERE u.role = 'instructor'
        GROUP BY u.full_name
        ORDER BY course_count DESC
        LIMIT 10
    """)
    result = cursor.fetchall()
    return pd.DataFrame(result, columns=["Instructor Name", "Number of Courses"])

def get_student_progress_data(cursor):
    cursor.execute("""
        SELECT u.full_name AS student_name, c.course_title AS course_title, e.progress
        FROM enrollments e
        JOIN users u ON e.user_ID = u.user_ID
        JOIN courses c ON e.course_ID = c.course_ID
        WHERE u.role = 'student'
    """)
    result = cursor.fetchall()
    return pd.DataFrame(result, columns=["student_name", "course_title", "progress"])

def plot_donut_chart(course_title, progress):
    # Ensure progress is clamped between 0 and 100
    progress = max(0, min(100, progress))
    remaining = 100 - progress

    df = pd.DataFrame({
        'Status': ['Completed', 'Remaining'],
        'Value': [progress, remaining]
    })

    fig = px.pie(
        df,
        names='Status',
        values='Value',
        hole=0.6,
        color='Status',
        color_discrete_map={'Completed': '#00cc96', 'Remaining': '#e0e0e0'}
    )

    fig.update_traces(
        textinfo='none',
        hovertemplate='%{label}: %{value:.1f}%',
    )

    fig.update_layout(
        showlegend=False,
        margin=dict(t=0, b=0, l=0, r=0),
        annotations=[
            dict(
                text=f"{progress:.0f}%",
                x=0.5, y=0.5,
                font_size=16,
                showarrow=False
            )
        ],
        height=250,
        width=250
    )

    return fig