import mysql
import streamlit as st

def get_chapters_by_course(cursor, course_id):
    # Fetch chapter details (including position) for the selected course
    cursor.execute("""
        SELECT c.chapter_ID, c.title, c.description, cc.position 
        FROM chapters c
        JOIN course_chapters cc ON c.chapter_ID = cc.chapter_ID
        WHERE cc.course_ID = %s
    """, (course_id,))
    return cursor.fetchall()




def delete_chapter_by_id(cursor, db_conn, chapter_id):
    """Delete chapter by ID."""
    cursor.execute("DELETE FROM chapters WHERE chapter_ID = %s", (chapter_id,))
    db_conn.commit()



def add_chapter(cursor, db_conn):
    """Page for adding a new chapter."""
    st.title("➕ Add New Chapter")
    
    # Create a form for the new chapter's details
    with st.form(key="add_chapter_form"):
        title = st.text_input("Chapter Title")
        description = st.text_area("Chapter Description")
        position = st.number_input("Position", min_value=1, value=1)

        # Submit button to add the chapter
        submit_button = st.form_submit_button("Add Chapter")
        
        if submit_button:
            # Add the new chapter to the database
            cursor.execute("INSERT INTO chapters (course_ID, title, description, position) VALUES (%s, %s, %s, %s)",
                           (st.session_state.selected_course_id, title, description, position))
            db_conn.commit()
            st.success("Chapter added successfully!")
            st.session_state.page_state = "view_chapters"  # Return to the chapters view
            st.rerun()

def delete_all_chapters_for_course(cursor, db_conn, course_id):
    """Delete all chapters for the given course."""
    try:
        # Step 1: Get the chapter IDs associated with the course
        cursor.execute("SELECT chapter_ID FROM course_chapters WHERE course_ID = %s", (course_id,))
        chapter_ids = cursor.fetchall()

        if not chapter_ids:
            st.warning("No chapters found for this course.")
            return

        # Step 2: Delete all rows in the 'course_chapters' table that match the course_id
        cursor.execute("DELETE FROM course_chapters WHERE course_ID = %s", (course_id,))
        db_conn.commit()

        # Step 3: Optionally, delete the chapters themselves from the 'chapters' table
        for chapter_id in chapter_ids:
            cursor.execute("DELETE FROM chapters WHERE chapter_ID = %s", (chapter_id[0],))
        
        db_conn.commit()

        st.success("All chapters have been deleted successfully!")
    
    except Exception as e:
        db_conn.rollback()  # Rollback in case of error
        st.error(f"An error occurred: {e}")

def edit_chapter(cursor, db_conn, chapter_id, new_title, new_description):
    """Edit chapter details in the database."""
    cursor.execute("""
        UPDATE chapters
        SET title = %s, description = %s
        WHERE chapter_ID = %s
    """, (new_title, new_description, chapter_id))
    db_conn.commit()
