import streamlit as st
import mysql
from content_modules.content_services import (
    get_contents_by_chapter,
    edit_content,
    delete_content_by_id,
    delete_all_contents_for_chapter,
    get_next_content_position
)

def content_management_view(cursor, db_conn):
    chapter_id = st.session_state.get("selected_chapter_id")
    st.write(f"Selected Chapter ID in content management view: {chapter_id}")  # Debug message

    if not chapter_id:
        st.error("No chapter selected.")
        return

    cursor.execute("SELECT title, description FROM chapters WHERE chapter_ID = %s", (chapter_id,))
    chapter = cursor.fetchone()

    if not chapter:
        st.error("Chapter not found.")
        return

    title, description = chapter
    st.title(f"📖 {title}")
    st.markdown(f"**Description**: {description}")

    contents = get_contents_by_chapter(cursor, chapter_id)

    if contents:
        st.subheader("📚 Chapter Contents")
        for content in contents:
            content_id, content_title, content_type, content_url, content_description, duration = content

            # Get content position from chapter_content table
            cursor.execute("""
                SELECT position FROM chapter_content
                WHERE chapter_ID = %s AND content_ID = %s
            """, (chapter_id, content_id))
            result = cursor.fetchone()
            content_position = result[0] if result else "N/A"

            with st.expander(f"📑 {content_title} ({content_type.capitalize()}) - Position: {content_position}"):
                st.markdown(f"**Description**: {content_description}")
                st.markdown(f"**Duration**: {duration} mins")
                st.markdown(f"🔗 [View Content]({content_url})")

                col1, col2 = st.columns(2)
                if col1.button(f"✏️ Edit Content {content_id}"):
                    st.session_state.page_state = "edit_content"
                    st.session_state.selected_content_id = content_id
                    st.rerun()

                if col2.button(f"🗑️ Delete Content {content_id}"):
                    delete_content_by_id(cursor, db_conn, content_id)
                    st.rerun()
    else:
        st.warning("No content found for this chapter.")

    st.markdown("<hr>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)

    if col1.button("🔙 Return to Chapters"):
        st.session_state.page_state = "view_chapters"
        st.rerun()

    if col2.button("➕ Add Content"):
        st.session_state.page_state = "add_content"
        st.rerun()

    if col3.button("🗑️ Delete All Contents"):
        delete_all_contents_for_chapter(cursor, db_conn, chapter_id)
        st.rerun()

def add_content_view(cursor, db_conn):
    chapter_id = st.session_state.get("selected_chapter_id")
    st.write(f"Selected Chapter ID for adding content: {chapter_id}")  # Debug message

    if not chapter_id:
        st.error("No chapter selected.")
        return

    cursor.execute("SELECT title, description FROM chapters WHERE chapter_ID = %s", (chapter_id,))
    chapter = cursor.fetchone()

    if not chapter:
        st.error("Chapter not found.")
        return

    title, description = chapter

    st.title(f"📖 Add Content to {title}")
    st.markdown(f"**Description**: {description}")
    st.subheader("Add New Content")

    content_title = st.text_input("📝 Content Title", max_chars=255)
    content_type = st.selectbox("📦 Content Type", ["video", "pdf", "quiz", "ppt", "text", "file"])
    content_description = st.text_area("📝 Description", max_chars=500)
    duration = st.number_input("⏱ Duration (in minutes)", min_value=1, step=1)
    content_url = st.text_input("🔗 Content URL (Unique URL)", max_chars=255)

    if st.button("➕ Add Content"):
        if not content_url or not content_title:
            st.error("Please provide both a content title and a content URL.")
        else:
            try:
                # Step 1: Check if content already exists with the same URL
                cursor.execute("SELECT content_ID FROM content WHERE content_url = %s", (content_url,))
                existing_content = cursor.fetchone()

                if existing_content:
                    content_id = existing_content[0]
                    cursor.execute("DELETE FROM chapter_content WHERE content_ID = %s", (content_id,))
                    db_conn.commit()
                    st.write(f"✅ Existing content with URL '{content_url}' replaced.")
                    cursor.execute("DELETE FROM content WHERE content_ID = %s", (content_id,))
                    db_conn.commit()

                # Step 2: Insert new content into the content table
                cursor.execute("""
                    INSERT INTO content (content_title, content_type, content_url, description, duration)
                    VALUES (%s, %s, %s, %s, %s)
                """, (content_title, content_type, content_url, content_description, duration))
                db_conn.commit()
                content_id = cursor.lastrowid
                st.write(f"✅ New content created successfully with ID {content_id}")

                # Step 3: Link new content to the chapter
                position = get_next_content_position(cursor, chapter_id)
                cursor.execute("""
                    INSERT INTO chapter_content (chapter_ID, content_ID, position)
                    VALUES (%s, %s, %s)
                """, (chapter_id, content_id, position))
                db_conn.commit()
                st.write(f"✅ Content linked to chapter ID {chapter_id} at position {position}")

                if st.button("➕ Add Another Content"):
                    st.rerun()

            except Exception as e:
                st.error(f"Error occurred while adding content: {e}")
                db_conn.rollback()

    col1, col2 = st.columns(2)
    if col1.button("🔙 Return to Chapter Management"):
        st.session_state.page_state = "view_chapters"
        st.rerun()

def edit_content_view(cursor, db_conn):
    content_id = st.session_state.get("selected_content_id")
    st.write(f"Selected Content ID for editing: {content_id}")  # Debug message

    if not content_id:
        st.error("No content selected for editing.")
        return

    # Fetch existing content details
    cursor.execute("SELECT content_title, content_type, content_url, description, duration FROM content WHERE content_ID = %s", (content_id,))
    content = cursor.fetchone()

    if not content:
        st.error("Content not found.")
        return

    content_title, content_type, content_url, content_description, duration = content

    # Ensure duration is an integer
    duration = int(duration)  # Convert duration to integer

    # Display the existing content information
    st.title(f"📝 Edit Content - {content_title}")
    st.subheader("Edit Content Details")

    new_content_title = st.text_input("📝 Content Title", value=content_title, max_chars=255)
    new_content_type = st.selectbox("📦 Content Type", ["video", "pdf", "quiz", "ppt", "text", "file"], index=["video", "pdf", "quiz", "ppt", "text", "file"].index(content_type))
    new_content_description = st.text_area("📝 Description", value=content_description, max_chars=500)
    new_duration = st.number_input("⏱ Duration (in minutes)", min_value=1, step=1, value=duration)
    new_content_url = st.text_input("🔗 Content URL (Unique URL)", value=content_url, max_chars=255)

    # Submit button to update content
    if st.button("✏️ Update Content"):
        if not new_content_url or not new_content_title:
            st.error("Please provide both a content title and a content URL.")
        else:
            try:
                # Step 1: Check if the URL already exists and is linked to a different content ID
                cursor.execute("SELECT content_ID FROM content WHERE content_url = %s AND content_ID != %s", (new_content_url, content_id))
                existing_content = cursor.fetchone()

                if existing_content:
                    st.warning(f"⚠️ Content URL '{new_content_url}' is already in use by another content item.")
                    return

                # Step 2: Update the content details in the 'content' table
                cursor.execute("""
                    UPDATE content
                    SET content_title = %s, content_type = %s, content_url = %s, description = %s, duration = %s
                    WHERE content_ID = %s
                """, (new_content_title, new_content_type, new_content_url, new_content_description, new_duration, content_id))
                db_conn.commit()

                st.success(f"✅ Content with ID {content_id} has been updated successfully!")

            except mysql.connector.Error as err:
                db_conn.rollback()
                st.error(f"🚫 MySQL Error while updating content {content_id}: {err}")
            except Exception as e:
                db_conn.rollback()
                st.error(f"🚫 An unexpected error occurred while updating content {content_id}: {e}")

    # Button to return to the previous view
    if st.button("🔙 Return to Content Management"):
        st.session_state.page_state = "view_content"
        st.rerun()

