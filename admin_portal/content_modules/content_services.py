# content_modules/content_services.py
from rich.console import Console
import streamlit as st
import mysql
console = Console()
def get_contents_by_chapter(cursor, chapter_id):
    cursor.execute("""
        SELECT c.content_ID, c.content_title, c.content_type, c.content_url, c.description, c.duration
        FROM content c
        JOIN chapter_content cc ON c.content_ID = cc.content_ID
        WHERE cc.chapter_ID = %s
        ORDER BY cc.position
    """, (chapter_id,))
    return cursor.fetchall()




def add_content(cursor, db_conn, chapter_id, title, content_type, content_data):
    cursor.execute(
        "INSERT INTO chapter_contents (chapter_ID, title, content_type, content_data) VALUES (%s, %s, %s, %s)",
        (chapter_id, title, content_type, content_data)
    )
    db_conn.commit()


def edit_content(cursor, db_conn, content_id, title, content_type, content_data):
    cursor.execute(
        "UPDATE chapter_contents SET title = %s, content_type = %s, content_data = %s WHERE content_ID = %s",
        (title, content_type, content_data, content_id)
    )
    db_conn.commit()


def delete_content_by_id(cursor, db_conn, content_id):
    try:
        # Step 0: Get the chapter ID linked to this content (before deletion)
        cursor.execute("SELECT chapter_ID FROM chapter_content WHERE content_ID = %s", (content_id,))
        result = cursor.fetchone()
        chapter_id = result[0] if result else None

        if not chapter_id:
            st.warning(f"⚠️ No chapter linked to content ID {content_id}. Skipping reordering.")
        
        # Step 1: Delete from chapter_content
        cursor.execute("DELETE FROM chapter_content WHERE content_ID = %s", (content_id,))
        db_conn.commit()

        # Step 2: Delete from content
        cursor.execute("DELETE FROM content WHERE content_ID = %s", (content_id,))
        db_conn.commit()

        # Step 3: Reorder remaining positions in chapter_content
        if chapter_id:
            cursor.execute("""
                SELECT content_ID FROM chapter_content
                WHERE chapter_ID = %s
                ORDER BY position ASC
            """, (chapter_id,))
            remaining_contents = cursor.fetchall()

            # Reassign positions
            for new_position, (c_id,) in enumerate(remaining_contents, start=1):
                cursor.execute("""
                    UPDATE chapter_content
                    SET position = %s
                    WHERE chapter_ID = %s AND content_ID = %s
                """, (new_position, chapter_id, c_id))
            db_conn.commit()

        st.success(f"✅ Content with ID {content_id} has been deleted and positions updated!")

    except mysql.connector.Error as err:
        db_conn.rollback()
        st.error(f"🚫 MySQL Error while deleting content {content_id}: {err}")
    except Exception as e:
        db_conn.rollback()
        st.error(f"🚫 An unexpected error occurred while deleting content {content_id}: {e}")



def delete_all_contents_for_chapter(cursor, db_conn, chapter_id):
    try:
        # Step 1: Delete all contents linked to the chapter in chapter_content table
        cursor.execute("DELETE FROM chapter_content WHERE chapter_ID = %s", (chapter_id,))
        db_conn.commit()
        print(f"✅ All contents for chapter with ID {chapter_id} deleted successfully from chapter_content.")
        
        # Step 2: Optionally, delete the contents from the content table if needed
        cursor.execute("DELETE FROM content WHERE content_ID NOT IN (SELECT content_ID FROM chapter_content)")
        db_conn.commit()
        print(f"✅ Orphaned contents not linked to any chapter deleted successfully.")
        
    except mysql.connector.Error as err:
        print(f"🚫 Error occurred while deleting all contents for chapter with ID {chapter_id}: {err}")
        db_conn.rollback()  # Rollback in case of error
    except Exception as e:
        print(f"🚫 An unexpected error occurred: {e}")
        db_conn.rollback()  # Rollback in case of error


def get_next_content_position(cursor, chapter_id):
    cursor.execute("""
        SELECT MAX(position) FROM chapter_content WHERE chapter_ID = %s
    """, (chapter_id,))
    result = cursor.fetchone()
    if result and result[0] is not None:
        return result[0] + 1
    else:
        return 1  # Start at position 1 if there is no content yet
