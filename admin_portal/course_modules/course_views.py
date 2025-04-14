import streamlit as st
from datetime import datetime
from course_modules.course_services import (
    get_all_courses, get_course_by_id, add_course_to_db, update_course_in_db, delete_course_by_id, update_total_hours_for_courses
)

def course_management_view(cursor, db_conn):
    st.title("📚 Course Management")

    # Add New Course Button
    if st.button("➕ Add New Course", use_container_width=True):
        st.session_state.page_state = "add_course"
        st.rerun()

    # Update Total Hours Button
    if st.button("🔄 Update Total Hours for All Courses", use_container_width=True):
        # Call the function to update total hours for all courses
        update_total_hours_for_courses(cursor, db_conn)
        st.success("✅ Total hours updated successfully for all courses!")

    # Fetch all courses
    courses = get_all_courses(cursor)
    if not courses:
        st.info("No courses found.")
        return

    # Iterate through each course and display details
    for course in courses:
        course_id, title, desc, category, level, price, thumb, hours, created_at, updated_at, learn, target, instructor = course

        # Use an expander to show course details
        with st.expander(f"📘 {title}"):
            # Display course details
            st.markdown(f"**🆔 ID**: {course_id}")
            st.markdown(f"**📚 Category**: {category}")
            st.markdown(f"**🎯 Level**: {level}")
            
            # Price formatted to two decimal places
            try:
                price = float(price)
            except ValueError:
                price = 0.0  # If price is invalid, default to 0.0
            st.markdown(f"**💰 Price**: ${price:.2f}")
            
            st.markdown(f"**⏱ Total Hours**: {hours}")
            st.markdown(f"**🗓 Created At**: {created_at}")
            st.markdown(f"**🔄 Updated At**: {updated_at}")
            st.markdown(f"**👨‍🏫 Instructor**: {instructor}")
            st.markdown(f"**📖 Description**: {desc[:200]}{'...' if len(desc) > 200 else ''}")
            st.markdown(f"**✅ What You'll Learn**: {learn}")
            st.markdown(f"**👥 Target Audience**: {target}")

            # Display course thumbnail (if available)
            if thumb:
                st.image(thumb, width=200)
            else:
                st.warning("No Thumbnail Available")

            # Add edit and delete buttons in columns
            col1, col2, col3 = st.columns(3)

            # Edit button
            if col1.button("✏️ Edit", key=f"edit_{course_id}"):
                st.session_state.page_state = "edit_course"
                st.session_state.selected_course_id = course_id
                st.rerun()

            # Delete button
            if col2.button("🗑️ Delete", key=f"del_{course_id}"):
                delete_course_by_id(cursor, db_conn, course_id)
                st.success("Course deleted successfully!")
                st.session_state.page_state = "home"  # Go back to the home page
                st.rerun()
            
            # Show button
            if col3.button("👁️ Show", key=f"show_{course_id}"):
                #delete_course_by_id(cursor, db_conn, course_id)
                #st.success("Course deleted successfully!")
                st.session_state.page_state = "home"  # Go back to the home page
                st.rerun()

            


def get_instructors(cursor):
    """Fetch all instructors from the users table."""
    cursor.execute("SELECT user_ID, full_name FROM users WHERE role = 'instructor';")
    # Change this to return a list of dictionaries for easy access by key
    instructors = cursor.fetchall()
    return [{"user_ID": instructor[0], "full_name": instructor[1]} for instructor in instructors]


def add_course_view(cursor, db_conn):
    st.title("➕ Add New Course")

    # Fetch all instructors
    instructors = get_instructors(cursor)
    instructor_options = [instructor["full_name"] for instructor in instructors]
    instructor_ids = {instructor["full_name"]: instructor["user_ID"] for instructor in instructors}

    with st.form("course_form"):
        title = st.text_input("Course Title")
        desc = st.text_area("Description")
        category = st.text_input("Category")
        level = st.selectbox("Level", ["Beginner", "Intermediate", "Advanced"])

        # Dropdown to select instructor by name
        instructor_name = st.selectbox("Instructor", instructor_options)
        instructor_id = instructor_ids[instructor_name]  # Get instructor ID based on selected name

        price = st.number_input("Price", value=0.0, step=0.5)
        thumbnail_url = st.text_input("Thumbnail URL")
        total_hours = st.number_input("Total Hours", value=0.0, step=0.5)
        learn = st.text_area("What You'll Learn")
        who_for = st.text_area("Who This Course is For")
        
        submitted = st.form_submit_button("Add Course")

        if submitted:
            data = {
                'course_title': title,
                'description': desc,
                'category': category,
                'level': level,
                'instructor_id': instructor_id,
                'price': price,
                'thumbnail_url': thumbnail_url,
                'total_hours': total_hours,
                'what_you_will_learn': learn,
                'who_this_course_is_for': who_for
            }
            course_id = add_course_to_db(cursor, db_conn, data)
            st.success(f"✅ Course '{title}' added with ID: {course_id}")
            st.session_state.page_state = "home"  # Ensure page state goes to courses
            st.rerun()

    if st.button("🔙 Back"):
        st.session_state.page_state = "home"
        st.rerun()


def edit_course_view(cursor, db_conn, course_id):
    # Fetch the course details by course_id
    course = get_course_by_id(cursor, course_id)
    if not course:
        st.error("❌ Course not found!")
        return

    # Display the course title
    st.title(f"✏️ Edit Course: {course['course_title']}")

    # Create a form to edit the course details
    with st.form("edit_course_form"):
        title = st.text_input("Course Title", value=course['course_title'])
        desc = st.text_area("Description", value=course['description'])
        category = st.text_input("Category", value=course['category'])
        
        # Providing a dropdown for selecting the level
        level = st.selectbox("Level", ["Beginner", "Intermediate", "Advanced"], index=["Beginner", "Intermediate", "Advanced"].index(course['level']))
        
        # Fetch all instructors and create options
        instructors = get_instructors(cursor)
        instructor_options = [instructor["full_name"] for instructor in instructors]
        instructor_ids = {instructor["full_name"]: instructor["user_ID"] for instructor in instructors}
        
        # Find the default instructor name based on the course data
        instructor_default_name = next((instructor["full_name"] for instructor in instructors if instructor["user_ID"] == course['instructor_id']), None)
        
        # Select an instructor from the dropdown
        instructor_name = st.selectbox("Instructor", instructor_options, index=instructor_options.index(instructor_default_name) if instructor_default_name else 0)
        
        # Get the corresponding instructor ID based on the selected instructor name
        instructor_id = instructor_ids[instructor_name]
        
        # Price input with step size of 0.5
        price = st.number_input("Price", value=float(course['price']), step=0.5)
        
        # Thumbnail URL input
        thumbnail_url = st.text_input("Thumbnail URL", value=course['thumbnail_url'])
        
        # Total hours input
        total_hours = st.number_input("Total Hours", value=float(course['total_hours']), step=0.5)
        
        # What You Will Learn and Who This Course Is For as text areas
        # Ensure that these fields are always treated as strings, even if they are empty or contain unexpected data
        learn = str(course['what_you_will_learn']) if course['what_you_will_learn'] else ''
        who_for = str(course['who_this_course_is_for']) if course['who_this_course_is_for'] else ''
        
        learn = st.text_area("What You'll Learn", value=learn)
        who_for = st.text_area("Who This Course Is For", value=who_for)
        
        # Submit button
        submitted = st.form_submit_button("Update Course")

        if submitted:
            # Collect the form data into a dictionary
            data = {
                'course_title': title,
                'description': desc,
                'category': category,
                'level': level,
                'instructor_id': instructor_id,  # Store the selected instructor ID
                'price': price,
                'thumbnail_url': thumbnail_url,
                'total_hours': total_hours,
                'what_you_will_learn': learn,  # Make sure this is treated as a string
                'who_this_course_is_for': who_for  # Make sure this is treated as a string
            }

            # Call the function to update course data in the database
            update_course_in_db(cursor, db_conn, course_id, data)

            # Show success message
            st.success("✅ Course updated successfully!")

            # Update page state and refresh the page
            st.session_state.page_state = "home"  # Set the page state back to home or the desired page
            st.rerun()  # Rerun the app to refresh the page



    if st.button("🔙 Back"):
        st.session_state.page_state = "home"
        st.rerun()