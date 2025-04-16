import streamlit as st
from uuid import uuid4

from student_enrollment_module.progress_services import (
    get_instructors,
    get_students,
    get_user_enrollments,
    get_instructor_courses,
    get_courses,
    update_student_progress,
    unenroll_student,
    get_review_for_course,
    add_or_update_review
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
                        for title, status, progress, course_id in enrollments:
                            st.markdown(f"<h5 style='font-weight: bold; font-size: 20px;'>{title}</h5>", unsafe_allow_html=True)

                            progress_percentage = int(progress)
                            if progress_percentage == 100:
                                status_color = "green"
                            elif progress_percentage >= 75:
                                status_color = "yellow"
                            else:
                                status_color = "red"

                            st.markdown(f"<p style='font-size:18px; color:{status_color};'>📘 Status: {status}, Progress: {progress}%</p>", unsafe_allow_html=True)

                            review = get_review_for_course(cursor, student_id, course_id)
                            sentiment_mapping = ["one", "two", "three", "four", "five"]
                            if review:
                                st.write(f"⭐ Rating: {review['rating']} star(s)")
                                st.write(f"📝 Review: {review['review']}")
                            else:
                                st.write("⭐ Rating: No rating yet")
                                st.write("📝 Review: No review yet")

                            st.write("Rate this course:")
                            selected = st.feedback("stars", key=f"stars_{student_id}_{course_id}")

                            review_text = st.text_area(
                                "Write a review (optional):", 
                                key=f"review_{student_id}_{course_id}"
                            )

                            if selected is not None:
                                st.markdown(f"You selected {sentiment_mapping[int(selected)]} star(s).")

                            if st.button("Submit Review", key=f"submit_review_{student_id}_{course_id}"):
                                if selected is not None:
                                    try:
                                        add_or_update_review(cursor, db_conn, student_id, course_id, int(selected+1), review_text)
                                        st.success("Your review has been submitted/updated!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Failed to submit review: {e}")
                                else:
                                    st.warning("Please select a star rating before submitting.")
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

    # Tab 3: Manage Student Enrollments
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

            enrolled_course_ids = set()

            if current_enrollments:
                for title, status, progress, course_id in current_enrollments:
                    enrolled_course_ids.add(course_id)

                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"**{title}** — Status: {status}, Progress: {progress:.1f}%")
                    with col2:
                        if st.button(f"❌ Unenroll", key=f"unenroll_{selected_student_id}_{course_id}"):
                            try:
                                unenroll_student(cursor, selected_student_id, title, db_conn)
                                st.success(f"Unenrolled from '{title}' successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error unenrolling: {e}")
            else:
                st.info("No current enrollments.")


            # Show all unenrolled courses with enroll buttons
            st.markdown("---")
            st.markdown(f"### ➕ Enroll {selected_student_label.split(' (')[0]} in a New Course")

            all_courses = get_courses(cursor)
            unenrolled_courses = [(cid, title) for cid, title in all_courses if cid not in enrolled_course_ids]

            if unenrolled_courses:
                for course_id, course_title in unenrolled_courses:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"**{course_title}**")
                    with col2:
                        if st.button("✅ Enroll", key=f"enroll_{selected_student_id}_{course_id}"):
                            try:
                                update_student_progress(cursor, db_conn, selected_student_id, course_title, 0)
                                st.success(f"Enrolled in '{course_title}' successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to enroll student: {e}")
            else:
                st.info("All courses already enrolled.")



