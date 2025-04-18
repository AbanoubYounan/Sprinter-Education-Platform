import streamlit as st
import plotly.graph_objects as go

from student_progress_module.progress_services import (
    get_student_progress_data,
    get_top_students_by_enrollments,
    get_top_instructors_by_courses,
    get_total_counts,
    plot_donut_chart
)

def progress_management_view(cursor, db_conn):
    st.title("📊 Progress Management Dashboard")

    # === METRICS ===
    total_students, total_instructors, total_courses = get_total_counts(cursor)
    col1, col2, col3 = st.columns(3)
    col1.metric("👨‍🎓 Total Students", total_students)
    col2.metric("👩‍🏫 Total Instructors", total_instructors)
    col3.metric("📚 Total Courses", total_courses)

    st.markdown("---")

    # === STUDENT LEADERBOARD ===
    st.subheader("🏅 Top Students by Enrollments")
    student_col1, student_col2 = st.columns([4, 1])
    with student_col1:
        st.markdown("#### 👨‍🎓 Students")
    with student_col2:
        num_students = st.number_input(
            "Top", min_value=1, max_value=20, value=5, step=1,
            label_visibility="collapsed", key="num_students"
        )

    top_students_df = get_top_students_by_enrollments(cursor).head(num_students)
    st.dataframe(top_students_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # === INSTRUCTOR LEADERBOARD ===
    st.subheader("🏅 Top Instructors by Course Count")
    inst_col1, inst_col2 = st.columns([4, 1])
    with inst_col1:
        st.markdown("#### 👩‍🏫 Instructors")
    with inst_col2:
        num_instructors = st.number_input(
            "Top", min_value=1, max_value=20, value=5, step=1,
            label_visibility="collapsed", key="num_instructors"
        )

    top_instructors_df = get_top_instructors_by_courses(cursor).head(num_instructors)
    st.dataframe(top_instructors_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # === STUDENT PROGRESS ===
    st.subheader("📈 Student Progress Overview")
    progress_df = get_student_progress_data(cursor)

    if progress_df.empty:
        st.warning("No progress data found.")
        return

    student_options = progress_df['student_name'].unique().tolist()
    selected_student = st.selectbox("Select Student", student_options)

    student_data = progress_df[progress_df['student_name'] == selected_student]

    if student_data.empty:
        st.info("No enrolled courses for this student.")
        return

    st.markdown("### Progress in Enrolled Courses")

    cols = st.columns(4)
    for i, (index, row) in enumerate(student_data.iterrows()):
        course_title = row['course_title']
        try:
            progress = float(row['progress'])
        except:
            progress = 0.0

        with cols[i % 4]:
            fig = plot_donut_chart(course_title, progress)

            # ✅ Add unique key to avoid duplication error
            chart_key = f"{selected_student}_{course_title}_{i}"
            st.plotly_chart(fig, use_container_width=True, key=chart_key)

            # ⬇ Course title directly under the figure
            st.markdown(
                f"<p style='text-align: center; font-size: 12px; color: #555; word-wrap: break-word;'>{course_title}</p>",
                unsafe_allow_html=True
            )
