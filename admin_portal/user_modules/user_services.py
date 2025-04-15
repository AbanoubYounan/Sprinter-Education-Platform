# user_module/user_services.py
# Backend logic: DB insert, delete, update

import uuid
import datetime
import json

def get_all_users(cursor):
    cursor.execute("""
        SELECT user_ID, full_name, email, password_hash, role, bio
        FROM users
    """)
    return cursor.fetchall()

def delete_user_by_id(cursor, db_conn, user_id):
    cursor.execute("DELETE FROM users WHERE user_ID = %s", (user_id,))
    db_conn.commit()

def add_user_to_db(cursor, db_conn, data):
    query = """
    INSERT INTO users (
        full_name, email, password_hash, role, bio,
        linkedin_url, github_url, profile_picture, preferences,
        education_level, years_of_experience, upload_cv_url,
        preferred_learning_platform, location, available_for_projects,
        programming_languages, tools_and_technologies, interests,
        preferred_project_types, verified, updated_at
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    now = datetime.datetime.now()

    cursor.execute(query, (
        data["full_name"], data["email"], data["password_hash"], data["role"], data["bio"],
        data["linkedin_url"], data["github_url"], data["profile_picture"], json.dumps(data["preferences"]),
        data["education_level"], int(data["years_of_experience"]), data["upload_cv_url"],
        data["preferred_learning_platform"], data["location"], data["available_for_projects"],
        data["programming_languages"], data["tools_and_technologies"], data["interests"],
        data["preferred_project_types"], data["verified"], now
    ))

    db_conn.commit()


def get_user_by_id(cursor, user_id):
    cursor.execute("SELECT * FROM users WHERE user_ID = %s", (user_id,))
    return cursor.fetchone()

def update_user_in_db(cursor, db_conn, user_id, data):
    query = """
        UPDATE users SET
            full_name = %s, email = %s, password_hash = %s, role = %s, bio = %s,
            linkedin_url = %s, github_url = %s, profile_picture = %s, preferences = %s,
            education_level = %s, years_of_experience = %s, upload_cv_url = %s,
            preferred_learning_platform = %s, location = %s, available_for_projects = %s,
            programming_languages = %s, tools_and_technologies = %s, interests = %s,
            preferred_project_types = %s, verified = %s, updated_at = %s
        WHERE user_ID = %s
    """
    now = datetime.datetime.now()
    cursor.execute(query, (
        data["full_name"], data["email"], data["password_hash"], data["role"], data["bio"],
        data["linkedin_url"], data["github_url"], data["profile_picture"], json.dumps(data["preferences"]),
        data["education_level"], int(data["years_of_experience"]), data["upload_cv_url"],
        data["preferred_learning_platform"], data["location"], data["available_for_projects"],
        data["programming_languages"], data["tools_and_technologies"], data["interests"],
        data["preferred_project_types"], data["verified"], now, user_id
    ))
    db_conn.commit()


