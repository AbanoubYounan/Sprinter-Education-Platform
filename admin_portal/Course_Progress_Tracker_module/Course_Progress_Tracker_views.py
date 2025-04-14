# Course_Progress_Tracker_module/Course_Progress_Tracker_views.py

import streamlit as st
from Course_Progress_Tracker_module.Course_Progress_Tracker_services import get_chapters_for_course, get_student_progress, update_student_progress, get_user_enrollments
from content_modules.content_services import get_contents_by_chapter
from student_enrollment_module.progress_services import get_students, get_courses

def course_progress_tracker_view(cursor, db_conn):
    st.title("🎯 Course Progress Tracker")

    # Step 1: Select student
    students = get_students(cursor)
    student_options = {f"{s[1]} (ID: {s[0]})": s[0] for s in students}
    selected_student_name = st.selectbox("👨‍🎓 Select Student", list(student_options.keys()))
    selected_student_id = student_options[selected_student_name]

    # Step 2: Show enrolled courses only
    cursor.execute("""
        SELECT c.course_ID, c.course_title
        FROM courses c
        JOIN enrollments e ON c.course_ID = e.course_ID
        WHERE e.user_ID = %s
    """, (selected_student_id,))
    enrolled_courses = cursor.fetchall()

    if not enrolled_courses:
        st.warning("⚠️ This student is not enrolled in any courses.")
        return

    course_options = {f"{c[1]} (ID: {c[0]})": c[0] for c in enrolled_courses}
    selected_course_name = st.selectbox("📚 Select Enrolled Course", list(course_options.keys()))
    selected_course_id = course_options[selected_course_name]

    # Step 3: Get chapters
    chapters = get_chapters_for_course(cursor, selected_course_id)

    updates = []

    for chapter in chapters:
        chapter_id, chapter_title, _, _ = chapter
        with st.expander(f"📘 {chapter_title}"):
            contents = get_contents_by_chapter(cursor, chapter_id)

            for content in contents:
                content_id = content[0]

                # Get content details
                cursor.execute("""
                    SELECT content_title, duration FROM content WHERE content_ID = %s
                """, (content_id,))
                content_data = cursor.fetchone()

                if content_data:
                    content_title, duration = content_data
                    is_watched = get_student_progress(cursor, selected_student_id, content_id)

                    cols = st.columns([0.8, 0.2])
                    with cols[0]:
                        st.markdown(f"**🎬 {content_title}** – {duration} min")
                    with cols[1]:
                        watched = st.checkbox(
                            "", value=is_watched, key=f"{selected_student_id}_{content_id}"
                        )

                    if watched != is_watched:
                        updates.append({
                            "student_id": selected_student_id,
                            "content_id": content_id,
                            "watched": watched,
                            "course_id": selected_course_id,
                            "chapter_id": chapter_id
                        })

    if st.button("💾 Submit Progress Updates"):
        if updates:
            for update in updates:
                msg = update_student_progress(
                    cursor=cursor,
                    db_conn=db_conn,
                    student_id=update["student_id"],
                    content_id=update["content_id"],
                    watched=update["watched"],
                    course_id=update["course_id"],
                    chapter_id=update["chapter_id"]
                )
                st.success(msg)
        else:
            st.info("📭 No changes to update.")











