# db_connection.py

import mysql.connector
from rich.console import Console

console = Console()

# --- Database Credentials ---
HOST = 'db.cl0oa2kwiw65.me-central-1.rds.amazonaws.com'
USER = 'admin'
PASSWORD = 'bo13QknuzQ5nKR95QU9i'
DB_NAME = 'CourseDataBase'

def connect_to_mysql(host=HOST, user=USER, password=PASSWORD, database=DB_NAME):
    try:
        db_conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )

        if db_conn.is_connected():
            console.print(f"✅ Successfully connected to the MySQL database: [bold cyan]{database}[/]", style="bold green")
            return db_conn
        else:
            console.print("❌ Connection failed.", style="bold red")
            return None

    except mysql.connector.Error as err:
        console.print(f"❌ Error connecting to DB: {err}", style="bold red")
        return None
