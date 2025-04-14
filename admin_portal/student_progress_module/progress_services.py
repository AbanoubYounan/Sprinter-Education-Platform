# student_progress_module/progress_services.py

import mysql.connector

def get_instructors(cursor):
    """Fetch all students from the users table."""
    cursor.execute("SELECT user_ID, full_name FROM users WHERE role = 'student';")
    return cursor.fetchall()

def get_student_progress(cursor, student_id):
    """Fetch progress of a student based on their content completions."""
    try:
        # Check if the student_content table exists
        cursor.execute("SHOW TABLES LIKE 'student_content';")
        result = cursor.fetchone()
        
        if result is None:
            raise Exception("student_content table does not exist. Please create it first.")
        
        # Query to fetch student's progress
        cursor.execute("""
            SELECT c.chapter_ID, c.title, 
                SUM(CASE WHEN sc.completed = 1 THEN 1 ELSE 0 END) / COUNT(*) * 100 AS progress
            FROM chapter_content c
            LEFT JOIN student_content sc ON c.content_ID = sc.content_ID 
            WHERE sc.student_ID = %s
            GROUP BY c.chapter_ID;
        """, (student_id,))
        
        progress = cursor.fetchall()
        return progress
    except mysql.connector.Error as err:
        raise Exception(f"Database error: {err}")
    except Exception as e:
        raise Exception(f"Error occurred while fetching progress: {e}")
