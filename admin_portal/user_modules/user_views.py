import streamlit as st
from user_modules.user_services import get_all_users, delete_user_by_id, get_user_by_id, update_user_in_db, add_user_to_db
import pandas as pd
from io import BytesIO

def user_management_view(cursor, db_conn):
    st.title("👥 User Management Panel")

    # Fetch users from DB
    users = get_all_users(cursor)  # Should return a list of tuples

    if not users:
        st.warning("No users found in the database.")
        return

    # Define DataFrame columns as per your schema
    df = pd.DataFrame(users, columns=[
        "ID", "Name", "Email", "Password", "Role", "Bio"
    ])

    df["Short ID"] = df["ID"].apply(lambda x: str(x)[:8])
    df["Bio"] = df["Bio"].fillna("—")  # Default display for empty bio

    st.markdown("### 🔎 Display Options")
    col1, col2 = st.columns([2, 2])

    with col1:
        num_display = st.number_input(
            "Number of users to show",
            min_value=1,
            max_value=len(df),
            value=min(10, len(df))
        )

    with col2:
        sort_col = st.selectbox(
            "Sort by",
            options=["Name", "Email", "Role"]
        )

    df = df.sort_values(by=sort_col).head(num_display)

    # --- Export to Excel ---
    export_df = df.drop(columns=["Password"])
    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        export_df.to_excel(writer, index=False, sheet_name="Users")
    excel_data = excel_buffer.getvalue()

    st.download_button(
        label="⬇️ Download Excel",
        data=excel_data,
        file_name="user_list.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Add user button
    if st.button("➕ Add User"):
        st.session_state.page_state = "add_user"
        st.rerun()

    st.markdown("### 📋 Users List")
    header_cols = st.columns([1.2, 2, 2.5, 1.2, 2.5, 0.6, 0.6, 0.6])
    headers = ["ID", "Name", "Email", "Role", "Bio", "✏️", "🗑️", "👁️"]
    for col, title in zip(header_cols, headers):
        col.markdown(f"**{title}**")

    for _, row in df.iterrows():
        row_cols = st.columns([1.2, 2, 2.5, 1.2, 2.5, 0.6, 0.6, 0.6])
        row_cols[0].markdown(f"{row['Short ID']}")
        row_cols[1].markdown(f"{row['Name']}")
        row_cols[2].markdown(f"{row['Email']}")
        row_cols[3].markdown(f"{row['Role']}")
        row_cols[4].markdown(f"{row['Bio']}")

        if row_cols[5].button("✏️", key=f"edit_{row['ID']}"):
            st.session_state.page_state = "edit_user"
            st.session_state.selected_user_id = row['ID']
            st.rerun()

        if row_cols[6].button("🗑️", key=f"delete_{row['ID']}"):
            delete_user_by_id(cursor, db_conn, row['ID'])
            db_conn.commit()
            st.success(f"✅ User '{row['Name']}' deleted.")
            st.rerun()

        if row_cols[7].button("👁️", key=f"view_{row['ID']}"):
            st.session_state.page_state = "show_user"
            st.session_state.selected_user_id = row['ID']
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
    verified = st.checkbox("Email Verified", value=user_data["verified"] or False)


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
            "preferred_project_types": preferred_project_types,
            "verified": verified 
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
    verified = st.checkbox("Email Verified", value=False)

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
                "preferred_project_types": preferred_project_types,
                "verified": verified 
            }
            add_user_to_db(cursor, db_conn, new_user_data)
            st.success("User added successfully!")
            st.session_state.page_state = "home"
            st.rerun()

    if st.button("🔙 Cancel"):
        st.session_state.page_state = "home"
        st.rerun()