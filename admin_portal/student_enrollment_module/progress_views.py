import streamlit as st
from uuid import uuid4

from student_enrollment_module.progress_services import (
    get_instructors,
    get_students,
    get_user_enrollments,
    get_instructor_courses,
    get_courses,
    update_student_progress
)

def enrollment_management_view(cursor, db_conn):
    st.title("📊 Enrollment Dashboard")

    tab1, tab2, tab3 = st.tabs(["👨‍🎓 Student Enrollments", "🧑‍🏫 Instructor Courses", "🎯 Manage Enrollments"])

    # Tab 1: Display Student Enrollments
    with tab1:
        st.subheader("All Students and Their Enrollments")
        students = get_students(cursor)

        if not students:
            st.info("No students found.")
        else:
            for student_id, full_name in students:
                with st.expander(f"👤 {full_name}", expanded=True):
                    st.markdown(f"<h4 style='color: #4CAF50;'>Enrollments:</h4>", unsafe_allow_html=True)

                    enrollments = get_user_enrollments(cursor, student_id)
                    if enrollments:
                        for title, status, progress in enrollments:
                            st.markdown(f"<h5 style='font-weight: bold; font-size: 20px;'>{title}</h5>", unsafe_allow_html=True)
                            
                            progress_percentage = int(progress)
                            if progress_percentage == 100:
                                status_color = "green"
                            elif progress_percentage >= 75:
                                status_color = "yellow"
                            else:
                                status_color = "red"
                            
                            st.markdown(f"<p style='font-size:18px; color:{status_color};'>📘 Status: {status}, Progress: {progress}%</p>", unsafe_allow_html=True)
                    else:
                        st.write("No enrollments.")

    # Tab 2: Display Instructors and Their Courses
    with tab2:
        st.subheader("All Instructors and Their Courses")
        instructors = get_instructors(cursor)

        if not instructors:
            st.info("No instructors found.")
        else:
            for instructor_id, full_name in instructors:
                courses = get_instructor_courses(cursor, instructor_id)
                with st.expander(f"🧑‍🏫 {full_name} ({len(courses)} course{'s' if len(courses) != 1 else ''})"):
                    if courses:
                        for course_title, course_id, category, level, price, total_hours in courses:
                            st.markdown(f"**{course_title}**")
                            st.write(f"- ID: `{course_id}`")
                            st.write(f"- Category: {category}")
                            st.write(f"- Level: {level}")
                            st.write(f"- Price: ${price}")
                            st.write(f"- Total Hours: {total_hours}")
                            st.markdown("---")
                    else:
                        st.write("No courses created.")

    # Tab 3: Manage Student Enrollments and Simulate Progress Watching
    with tab3:
        st.subheader("🎯 Manage Student Enrollments")

        students = get_students(cursor)
        if not students:
            st.warning("No students available.")
        else:
            student_names = {f"{name} ({uid})": uid for uid, name in students}
            selected_student_label = st.selectbox("Select a student", list(student_names.keys()))
            selected_student_id = student_names[selected_student_label]

            st.markdown(f"### 📚 Current Enrollments for {selected_student_label.split(' (')[0]}")
            current_enrollments = get_user_enrollments(cursor, selected_student_id)

            if current_enrollments:
                for title, status, progress in current_enrollments:
                    st.write(f"**{title}** — Status: {status}, Progress: {progress}%")
            else:
                st.info("No current enrollments.")

            st.markdown("---")
            st.markdown(f"### ➕ Add New Courses for {selected_student_label.split(' (')[0]}")

            all_courses = get_courses(cursor)
            enrolled_titles = [title for title, _, _ in current_enrollments]

            available_courses = [(cid, title) for cid, title in all_courses if title not in enrolled_titles]

            for course_id, course_title in available_courses:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"**{course_title}**")
                with col2:
                    if st.button("Enroll", key=f"enroll_{course_id}"):
                        enroll_id = str(uuid4())
                        try:
                            cursor.execute(
                                '''INSERT INTO enrollments (enroll_ID, user_ID, course_ID, status, progress)
                                VALUES (%s, %s, %s, 'Active', 0.0)''',
                                (enroll_id, selected_student_id, course_id)
                            )
                            db_conn.commit()
                            st.success(f"Enrolled in '{course_title}'!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to enroll: {e}")

            st.markdown("---")
