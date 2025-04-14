import streamlit as st
from chapter_modules.chapter_services import get_chapters_by_course, delete_chapter_by_id, delete_all_chapters_for_course, edit_chapter
from course_modules.course_services import get_all_courses

from rich.console import Console
import random
import string

# Initialize console for output (optional for logging purposes)
console = Console()


# MAIN VIEW
def chapter_management_view(cursor, db_conn):
    st.title("📚 Chapter Management")

    # Fetch all courses
    courses = get_all_courses(cursor)
    if not courses:
        st.info("No courses found.")
        return

    for course in courses:
        course_id, title, desc, category, level, price, thumb, hours, created_at, updated_at, learn, target, instructor = course

        with st.expander(f"📘 {title}"):
            st.markdown(f"**🆔 ID**: {course_id}")
            st.markdown(f"**📚 Category**: {category}")
            st.markdown(f"**🎯 Level**: {level}")
            try:
                price = float(price)
            except ValueError:
                price = 0.0
            st.markdown(f"**💰 Price**: ${price:.2f}")
            st.markdown(f"**⏱ Total Hours**: {hours}")
            st.markdown(f"**🗓 Created At**: {created_at}")
            st.markdown(f"**🔄 Updated At**: {updated_at}")
            st.markdown(f"**👨‍🏫 Instructor**: {instructor}")
            st.markdown(f"**📖 Description**: {desc[:200]}{'...' if len(desc) > 200 else ''}")
            st.markdown(f"**✅ What You'll Learn**: {learn}")
            st.markdown(f"**👥 Target Audience**: {target}")
            if thumb:
                st.image(thumb, width=200)
            else:
                st.warning("No Thumbnail Available")

            col1, _ = st.columns(2)
            if col1.button(f"👁️ Show Chapters for {title}", key=f"show_chapters_{course_id}"):
                st.session_state.selected_course_id = course_id
                st.session_state.page_state = "view_chapters"
                st.rerun()


# VIEW CHAPTERS
def view_chapters(cursor, db_conn):
    course_id = st.session_state.get("selected_course_id")
    if not course_id:
        st.error("No course selected.")
        return

    cursor.execute("SELECT course_title FROM courses WHERE course_ID = %s", (course_id,))
    course = cursor.fetchone()
    if not course:
        st.error("Course not found.")
        return
    course_title = course[0]

    st.title(f"📖 Chapters for Course: {course_title}")
    chapters = get_chapters_by_course(cursor, course_id)

    if not chapters:
        st.info("No chapters found for this course.")

    for idx, chapter in enumerate(chapters):
        chapter_id, title, description, position = chapter
        with st.expander(f"📘 Chapter: {title}"):
            st.markdown(f"**🆔 ID**: {chapter_id}")
            st.markdown(f"**📜 Title**: {title}")
            st.markdown(f"**📝 Description**: {description[:200]}{'...' if len(description) > 200 else ''}")
            st.markdown(f"**📍 Position**: {position}")

            col1, col2, col3 = st.columns(3)

            if col1.button("✏️ Edit", key=f"edit_{chapter_id}_{idx}"):
                st.session_state.selected_chapter_id = chapter_id
                st.session_state.page_state = "edit_chapter"
                st.rerun()

            if col2.button("🗑️ Delete", key=f"delete_{chapter_id}_{idx}"):
                delete_chapter_by_id(cursor, db_conn, chapter_id)

                # Reorder remaining chapters
                cursor.execute("SELECT chapter_ID FROM course_chapters WHERE course_ID = %s ORDER BY position", (course_id,))
                chapter_ids = cursor.fetchall()
                for new_pos, (cid,) in enumerate(chapter_ids, start=1):
                    cursor.execute(
                        "UPDATE course_chapters SET position = %s WHERE course_ID = %s AND chapter_ID = %s",
                        (new_pos, course_id, cid)
                    )
                db_conn.commit()

                st.success("Chapter deleted and positions updated successfully!")
                st.rerun()

            # In the "👁️ Show" button logic inside the 'view_chapters' function:
            if col3.button("👁️ Show", key=f"show_{chapter_id}_{idx}"):
                st.session_state.selected_chapter_id = chapter_id  # Ensure selected_chapter_id is set
                st.write(f"Selected Chapter ID set to: {chapter_id}")  # Debug message
                st.session_state.page_state = "view_content"  # Change page state to view content
                st.rerun()  # Rerun to navigate to content management view


    st.markdown("<hr>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)

    if col1.button("🔙 Return to Home"):
        st.session_state.page_state = "home"
        st.rerun()

    if col2.button("➕ Add New Chapter"):
        st.session_state.page_state = "add_chapter"
        st.rerun()

    if col3.button("🗑️ Delete All Chapters"):
        delete_all_chapters_for_course(cursor, db_conn, course_id)
        st.success("All chapters deleted successfully!")
        st.rerun()


# ADD CHAPTER
def add_chapter_view(cursor, db_conn):
    st.title("➕ Add New Chapter")

    course_id = st.session_state.get("selected_course_id")
    if not course_id:
        st.error("No course selected.")
        return

    title = st.text_input("Chapter Title")
    description = st.text_area("Chapter Description")

    if st.button("Add Chapter"):
        if title and description:
            cursor.execute("SELECT COUNT(*) FROM course_chapters WHERE course_ID = %s", (course_id,))
            position = cursor.fetchone()[0] + 1

            cursor.execute("INSERT INTO chapters (title, description) VALUES (%s, %s)", (title, description))
            db_conn.commit()

            cursor.execute("SELECT LAST_INSERT_ID()")
            chapter_id = cursor.fetchone()[0]

            cursor.execute(
                "INSERT INTO course_chapters (course_ID, chapter_ID, position) VALUES (%s, %s, %s)",
                (course_id, chapter_id, position)
            )
            db_conn.commit()

            st.success(f"Chapter '{title}' added at position {position}!")
            st.session_state.page_state = "view_chapters"
            st.rerun()
        else:
            st.error("Please fill in all fields.")


# EDIT CHAPTER
def edit_chapter_view(cursor, db_conn, chapter_id):
    cursor.execute("SELECT title, description FROM chapters WHERE chapter_ID = %s", (chapter_id,))
    chapter = cursor.fetchone()

    if not chapter:
        st.error("Chapter not found.")
        return

    current_title, current_description = chapter
    st.title(f"✏️ Edit Chapter: {current_title}")

    new_title = st.text_input("New Chapter Title", value=current_title)
    new_description = st.text_area("New Chapter Description", value=current_description)

    if st.button("Save Changes"):
        if new_title and new_description:
            edit_chapter(cursor, db_conn, chapter_id, new_title, new_description)
            st.success("Chapter updated successfully!")
            st.session_state.page_state = "view_chapters"
            st.rerun()
        else:
            st.error("Please fill in both the title and description fields.")
