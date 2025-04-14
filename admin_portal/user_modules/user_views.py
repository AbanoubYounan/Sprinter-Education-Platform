import streamlit as st
from user_modules.user_services import get_all_users, delete_user_by_id, get_user_by_id, update_user_in_db, add_user_to_db

def user_management_view(cursor, db_conn):
    st.title("👥 User Management Panel")

    # Inject custom CSS for styling the button
    st.markdown("""
        <style>
        .small-button {
            font-size: 18px;
            background-color: #4CAF50;
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            border: none;
            cursor: pointer;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            transition: background-color 0.3s, transform 0.3s;
        }
        .small-button:hover {
            background-color: #45a049;
            transform: scale(1.1);
        }
        </style>
    """, unsafe_allow_html=True)

    # Small and impressive "Add User" button
    if st.button("➕ Add User", key="add_user_button", help="Click to add a new user"):
        st.session_state.page_state = "add_user"
        st.rerun()

    # Get users
    users = get_all_users(cursor)
    if not users:
        st.warning("No users found in the database.")
        return

    st.markdown("## 📋 Users List")
    for user in users:
        user_id, name, email, _, role, bio = user[:6]
        col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([1.5, 2.5, 3, 1.5, 3, 0.7, 0.7, 0.7])
        with col1: st.write(user_id)
        with col2: st.write(name)
        with col3: st.write(email)
        with col4: st.write(role)
        with col5: st.write(bio)

        with col6:
            if st.button("✏️", key=f"edit_{user_id}"):
                st.session_state.page_state = "edit_user"
                st.session_state.selected_user_id = user_id
                st.rerun()

        with col7:
            if st.button("🗑️", key=f"delete_{user_id}"):
                delete_user_by_id(cursor, db_conn, user_id)
                st.success(f"User '{name}' deleted.")
                st.rerun()

        with col8:
            if st.button("👁️", key=f"show_{user_id}"):
                st.session_state.page_state = "show_user"
                st.session_state.selected_user_id = user_id
                st.rerun()

def show_user_view(cursor, db_conn, user_id):
    st.title("👁️ User Details")

    user = get_user_by_id(cursor, user_id)
    if user is None:
        st.error("User not found.")
        return

    columns = [desc[0] for desc in cursor.description]
    user_data = dict(zip(columns, user))

    # Get the image URL
    image_url = user_data.get("profile_picture")
    
    if image_url:
        try:
            # Display the image
            st.image(image_url, width=200)
        except Exception as e:
            st.error(f"Error loading image: {e}")
    else:
        st.warning("No profile picture available.")
    
    # Display other user details
    for key, value in user_data.items():
        st.markdown(f"**{key.replace('_', ' ').title()}**: {value}")

    if st.button("🔙 Back to Users List"):
        st.session_state.page_state = "home"
        st.session_state.selected_user_id = None
        st.rerun()

def edit_user_view(cursor, db_conn, user_id):
    st.title("✏️ Edit User")
    user = get_user_by_id(cursor, user_id)
    if not user:
        st.error("User not found.")
        return

    columns = [desc[0] for desc in cursor.description]
    user_data = dict(zip(columns, user))

    full_name = st.text_input("Full Name", user_data["full_name"])
    email = st.text_input("Email", user_data["email"])
    password_visible = st.checkbox("Show Password")
    password_input_type = "default" if password_visible else "password"
    password_hash = st.text_input("Password Hash", user_data["password_hash"], type=password_input_type)
    role = st.selectbox("Role", ["student", "instructor", "admin"], index=["student", "instructor", "admin"].index(user_data["role"]))
    bio = st.text_area("Bio", user_data["bio"])
    linkedin_url = st.text_input("LinkedIn URL", user_data["linkedin_url"])
    github_url = st.text_input("GitHub URL", user_data["github_url"])
    profile_picture = st.text_input("Profile Picture URL", user_data["profile_picture"])
    preferences = st.text_area("Preferences (JSON)", user_data["preferences"] or "")
    education_level = st.text_input("Education Level", user_data["education_level"])
    years_of_experience = st.number_input("Years of Experience", value=user_data["years_of_experience"] or 0, step=1)
    upload_cv_url = st.text_input("CV URL", user_data["upload_cv_url"])
    preferred_learning_platform = st.text_input("Preferred Learning Platform", user_data["preferred_learning_platform"])
    location = st.text_input("Location", user_data["location"])
    available_for_projects = st.checkbox("Available for Projects", value=user_data["available_for_projects"] or False)
    programming_languages = st.text_area("Programming Languages", user_data["programming_languages"])
    tools_and_technologies = st.text_area("Tools & Technologies", user_data["tools_and_technologies"])
    interests = st.text_area("Interests", user_data["interests"])
    preferred_project_types = st.text_area("Preferred Project Types", user_data["preferred_project_types"])

    if st.button("✅ Save Changes"):
        updated_data = {
            "full_name": full_name,
            "email": email,
            "password_hash": password_hash,
            "role": role,
            "bio": bio,
            "linkedin_url": linkedin_url,
            "github_url": github_url,
            "profile_picture": profile_picture,
            "preferences": preferences,
            "education_level": education_level,
            "years_of_experience": years_of_experience,
            "upload_cv_url": upload_cv_url,
            "preferred_learning_platform": preferred_learning_platform,
            "location": location,
            "available_for_projects": available_for_projects,
            "programming_languages": programming_languages,
            "tools_and_technologies": tools_and_technologies,
            "interests": interests,
            "preferred_project_types": preferred_project_types
        }
        update_user_in_db(cursor, db_conn, user_id, updated_data)
        st.success("User updated successfully!")
        st.session_state.page_state = "home"
        st.session_state.selected_user_id = None
        st.rerun()

    if st.button("🔙 Cancel"):
        st.session_state.page_state = "home"
        st.session_state.selected_user_id = None
        st.rerun()

def add_user_view(cursor, db_conn):
    st.title("➕ Add New User")

    full_name = st.text_input("Full Name")
    email = st.text_input("Email")
    password_hash = st.text_input("Password Hash", type="password")
    role = st.selectbox("Role", ["student", "instructor", "admin"])
    bio = st.text_area("Bio")
    linkedin_url = st.text_input("LinkedIn URL")
    github_url = st.text_input("GitHub URL")
    profile_picture = st.text_input("Profile Picture URL")
    preferences = st.text_area("Preferences (JSON)")
    education_level = st.text_input("Education Level")
    years_of_experience = st.number_input("Years of Experience", step=1)
    upload_cv_url = st.text_input("CV URL")
    preferred_learning_platform = st.text_input("Preferred Learning Platform")
    location = st.text_input("Location")
    available_for_projects = st.checkbox("Available for Projects")
    programming_languages = st.text_area("Programming Languages")
    tools_and_technologies = st.text_area("Tools & Technologies")
    interests = st.text_area("Interests")
    preferred_project_types = st.text_area("Preferred Project Types")

    if st.button("✅ Add User"):
        if not full_name or not email or not password_hash:
            st.warning("Full name, email, and password are required.")
        else:
            new_user_data = {
                "full_name": full_name,
                "email": email,
                "password_hash": password_hash,
                "role": role,
                "bio": bio,
                "linkedin_url": linkedin_url,
                "github_url": github_url,
                "profile_picture": profile_picture,
                "preferences": preferences,
                "education_level": education_level,
                "years_of_experience": years_of_experience,
                "upload_cv_url": upload_cv_url,
                "preferred_learning_platform": preferred_learning_platform,
                "location": location,
                "available_for_projects": available_for_projects,
                "programming_languages": programming_languages,
                "tools_and_technologies": tools_and_technologies,
                "interests": interests,
                "preferred_project_types": preferred_project_types
            }
            add_user_to_db(cursor, db_conn, new_user_data)
            st.success("User added successfully!")
            st.session_state.page_state = "home"
            st.rerun()

    if st.button("🔙 Cancel"):
        st.session_state.page_state = "home"
        st.rerun()