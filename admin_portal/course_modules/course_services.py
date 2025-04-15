import uuid
from datetime import datetime
import mysql.connector

def get_all_courses(cursor):
    """
    Fetch all courses with detailed information including instructor info.
    """
    query = '''
        SELECT
            c.course_ID,
            c.course_title,
            c.description,
            c.category,
            c.level,
            c.price,
            c.thumbnail_url,
            c.total_hours,
            c.created_at,
            c.updated_at,
            c.what_you_will_learn,
            c.who_this_course_is_for,
            u.full_name AS instructor_name
        FROM courses c
        JOIN users u ON c.instructor_id = u.user_ID
        ORDER BY c.created_at DESC;
    '''
    cursor.execute(query)
    return cursor.fetchall()


def get_course_by_id(cursor, course_id):
    # Query to get all columns from the courses table
    query = "SELECT * FROM courses WHERE course_ID = %s"
    cursor.execute(query, (course_id,))
    result = cursor.fetchone()
    
    if result:
        # Assuming the result contains all the columns in the correct order
        columns = [
            "course_ID", "course_title", "description", "category", "level",
            "instructor_id", "price", "thumbnail_url", "total_hours", "created_at",
            "updated_at", "what_you_will_learn", "who_this_course_is_for"
        ]
        return dict(zip(columns, result))  # Convert the tuple to a dictionary
    return None




def add_course_to_db(cursor, db_conn, course_data):
    """
    Add a new course to the database with all its details.
    Checks if the instructor exists before adding the course.
    """
    # Check if instructor exists
    instructor_check_query = "SELECT 1 FROM users WHERE user_ID = %s"
    cursor.execute(instructor_check_query, (course_data.get('instructor_id'),))
    if not cursor.fetchone():
        raise ValueError("Instructor with this ID does not exist.")

    # Generate a unique course ID using UUID
    course_ID = str(uuid.uuid4())

    # Add course_ID to the course_data dictionary
    course_data['course_ID'] = course_ID

    query = """
        INSERT INTO courses 
        (course_ID, course_title, description, category, level, instructor_id, price, 
        thumbnail_url, total_hours, what_you_will_learn, who_this_course_is_for)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """

    # Execute the query with course_data values including the generated course_ID
    cursor.execute(query, (
        course_data.get('course_ID'),
        course_data.get('course_title', ''),
        course_data.get('description', ''),
        course_data.get('category', ''),
        course_data.get('level', ''),
        course_data.get('instructor_id', ''),
        course_data.get('price', 0.0),
        course_data.get('thumbnail_url', ''),
        course_data.get('total_hours', 0.0),
        course_data.get('what_you_will_learn', ''),
        course_data.get('who_this_course_is_for', '')
    ))

    # Commit the transaction to the database
    db_conn.commit()

    # Return the generated course_ID for confirmation or further use
    return course_ID


def update_course_in_db(cursor, db_conn, course_id, data):
    # Ensure that the 'instructor_id' is converted to an integer if necessary
    try:
        query = """
            UPDATE courses
            SET 
                course_title = %s,
                description = %s,
                category = %s,
                level = %s,
                instructor_id = %s,
                price = %s,
                thumbnail_url = %s,
                total_hours = %s,
                what_you_will_learn = %s,
                who_this_course_is_for = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE course_ID = %s
        """

        # Prepare values to update
        values = (
            data['course_title'], 
            data['description'],
            data['category'],
            data['level'],
            data['instructor_id'],
            data['price'],
            data['thumbnail_url'],
            data['total_hours'],
            data['what_you_will_learn'],
            data['who_this_course_is_for'],
            course_id
        )

        # Execute the query with values
        cursor.execute(query, values)
        db_conn.commit()  # Commit changes to the database
    except Exception as e:
        print(f"❌ Failed to update course: {e}")


def delete_course_by_id(cursor, db_conn, course_id):
    try:
        cursor.execute("DELETE FROM courses WHERE course_ID = %s", (course_id,))
        db_conn.commit()  # Ensure the changes are saved to the database
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        db_conn.rollback()  # Rollback the changes if there's an error

def update_total_hours_for_courses(cursor, conn):
    fetch_courses_query = "SELECT course_ID, total_hours FROM courses"
    cursor.execute(fetch_courses_query)
    courses = cursor.fetchall()

    for course_id, old_hours in courses:
        new_hours_query = '''
            SELECT SUM(content.duration) / 60.0
            FROM chapter_content cc
            JOIN content ON cc.content_ID = content.content_ID
            WHERE cc.chapter_ID IN (
                SELECT chapter_ID FROM course_chapters WHERE course_ID = %s
            )
        '''
        cursor.execute(new_hours_query, (course_id,))
        result = cursor.fetchone()
        new_hours = result[0] if result[0] is not None else 0.0

        if old_hours != new_hours:
            print(f"⏱ Course ID: {course_id} | Old Hours: {old_hours:.2f} | New Hours: {new_hours:.2f}")
            update_query = "UPDATE courses SET total_hours = %s WHERE course_ID = %s"
            cursor.execute(update_query, (new_hours, course_id))

    try:
        conn.commit()
        print("✅ Total hours updated successfully for all courses.")
    except Exception as e:
        print(f"❌ Error committing total hour updates: {e}")
        conn.rollback()

def get_average_rating_for_course(cursor, course_id):
    cursor.execute("""
        SELECT AVG(rating) 
        FROM course_reviews 
        WHERE course_ID = %s
    """, (course_id,))
    result = cursor.fetchone()
    return round(result[0], 1) if result and result[0] else 0.0

def render_star_rating(avg_rating):
    full_star = "⭐"
    empty_star = "☆"
    rating = int(avg_rating)
    stars = full_star * rating + empty_star * (5 - rating)
    return f"{stars} ({avg_rating}/5)"

