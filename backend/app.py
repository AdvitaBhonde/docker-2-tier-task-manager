import os
import time
import sqlite3
import pymysql
from pymysql.cursors import DictCursor
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Environment configuration with safe defaults
DB_HOST = os.getenv("MYSQL_HOST", "localhost")
DB_USER = os.getenv("MYSQL_USER", "taskuser")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD", "taskpassword123")
DB_NAME = os.getenv("MYSQL_DATABASE", "taskdb")
DB_PORT = int(os.getenv("MYSQL_PORT", 3306))

# Flag to track active database backend ('mysql' or 'sqlite')
USE_SQLITE = False
SQLITE_DB_PATH = os.path.join(os.path.dirname(__file__), "tasks.db")


def get_sqlite_connection():
    """Establish connection to SQLite database for local non-docker testing."""
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_db_connection():
    """Return an active connection for either MySQL or SQLite."""
    if USE_SQLITE:
        return get_sqlite_connection()
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT,
        cursorclass=DictCursor,
        autocommit=True,
    )


def init_db():
    """Attempt MySQL connection; if unavailable, seamlessly fall back to local SQLite."""
    global USE_SQLITE

    # Attempt MySQL connection (tries max 3 times if running locally)
    max_retries = 3 if DB_HOST == "localhost" or DB_HOST == "127.0.0.1" else 10
    print(f"Connecting to database at {DB_HOST}:{DB_PORT}...")

    for attempt in range(1, max_retries + 1):
        try:
            conn = pymysql.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                port=DB_PORT,
                cursorclass=DictCursor,
                autocommit=True,
            )
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS tasks (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        title VARCHAR(255) NOT NULL,
                        description TEXT,
                        status ENUM('pending', 'completed') DEFAULT 'pending',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    """
                )
            conn.close()
            USE_SQLITE = False
            print("Successfully connected to MySQL database.")
            return True
        except Exception as err:
            print(f"MySQL connection attempt {attempt}/{max_retries} failed: {err}")
            if attempt < max_retries:
                time.sleep(2)

    # Fallback to SQLite for zero-setup local execution without Docker/MySQL
    print("\n[NOTICE] MySQL unavailable. Falling back to local SQLite database (tasks.db)...")
    USE_SQLITE = True
    try:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        # Seed initial data if empty
        cursor.execute("SELECT COUNT(*) FROM tasks;")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                "INSERT INTO tasks (title, description, status) VALUES (?, ?, ?);",
                [
                    ("Set up Flask Backend", "Python Flask API running locally without Docker.", "completed"),
                    ("Deploy on AWS EC2", "Launch EC2 instance and run Docker Compose in the cloud.", "pending"),
                    ("Prepare GitHub Repo", "Upload project code to GitHub for portfolio.", "pending")
                ]
            )
            conn.commit()
        conn.close()
        print("Successfully initialized SQLite database (tasks.db).")
        return True
    except Exception as sq_err:
        print(f"SQLite initialization error: {sq_err}")
        return False


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint to verify backend service and DB status."""
    try:
        conn = get_db_connection()
        conn.close()
        db_type = "sqlite" if USE_SQLITE else "mysql"
        return jsonify({"status": "healthy", "database": db_type}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500


@app.route("/api/tasks", methods=["GET"])
def get_tasks():
    """Fetch all tasks ordered by creation date descending."""
    try:
        conn = get_db_connection()
        if USE_SQLITE:
            cursor = conn.cursor()
            cursor.execute("SELECT id, title, description, status, datetime(created_at, 'localtime') AS created_at FROM tasks ORDER BY id DESC;")
            rows = cursor.fetchall()
            tasks = [dict(row) for row in rows]
        else:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id, title, description, status, DATE_FORMAT(created_at, '%Y-%m-%d %H:%i:%s') AS created_at FROM tasks ORDER BY created_at DESC, id DESC;")
                tasks = cursor.fetchall()
        conn.close()
        return jsonify({"success": True, "data": tasks}), 200
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to retrieve tasks: {str(e)}"}), 500


@app.route("/api/tasks", methods=["POST"])
def create_task():
    """Create a new task."""
    data = request.get_json() or {}
    title = data.get("title", "").strip()
    description = data.get("description", "").strip()

    if not title:
        return jsonify({"success": False, "error": "Title is required"}), 400

    try:
        conn = get_db_connection()
        if USE_SQLITE:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO tasks (title, description, status) VALUES (?, ?, 'pending');", (title, description))
            conn.commit()
            task_id = cursor.lastrowid
        else:
            with conn.cursor() as cursor:
                sql = "INSERT INTO tasks (title, description, status) VALUES (%s, %s, 'pending');"
                cursor.execute(sql, (title, description))
                task_id = cursor.lastrowid
        conn.close()
        return jsonify({"success": True, "message": "Task created successfully", "task_id": task_id}), 201
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to create task: {str(e)}"}), 500


@app.route("/api/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    """Update task status ('completed' or 'pending') or task content."""
    data = request.get_json() or {}
    status = data.get("status")
    title = data.get("title")
    description = data.get("description")

    try:
        conn = get_db_connection()
        if USE_SQLITE:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM tasks WHERE id = ?;", (task_id,))
            if not cursor.fetchone():
                conn.close()
                return jsonify({"success": False, "error": "Task not found"}), 404

            updates = []
            params = []
            if status in ["pending", "completed"]:
                updates.append("status = ?")
                params.append(status)
            if title is not None:
                if not title.strip():
                    conn.close()
                    return jsonify({"success": False, "error": "Title cannot be empty"}), 400
                updates.append("title = ?")
                params.append(title.strip())
            if description is not None:
                updates.append("description = ?")
                params.append(description.strip())

            if not updates:
                conn.close()
                return jsonify({"success": False, "error": "No fields to update"}), 400

            params.append(task_id)
            sql = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?;"
            cursor.execute(sql, tuple(params))
            conn.commit()
        else:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM tasks WHERE id = %s;", (task_id,))
                if not cursor.fetchone():
                    conn.close()
                    return jsonify({"success": False, "error": "Task not found"}), 404

                updates = []
                params = []
                if status in ["pending", "completed"]:
                    updates.append("status = %s")
                    params.append(status)
                if title is not None:
                    if not title.strip():
                        conn.close()
                        return jsonify({"success": False, "error": "Title cannot be empty"}), 400
                    updates.append("title = %s")
                    params.append(title.strip())
                if description is not None:
                    updates.append("description = %s")
                    params.append(description.strip())

                if not updates:
                    conn.close()
                    return jsonify({"success": False, "error": "No fields to update"}), 400

                params.append(task_id)
                sql = f"UPDATE tasks SET {', '.join(updates)} WHERE id = %s;"
                cursor.execute(sql, tuple(params))

        conn.close()
        return jsonify({"success": True, "message": f"Task {task_id} updated successfully"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to update task: {str(e)}"}), 500


@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    """Delete a task by ID."""
    try:
        conn = get_db_connection()
        if USE_SQLITE:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM tasks WHERE id = ?;", (task_id,))
            if not cursor.fetchone():
                conn.close()
                return jsonify({"success": False, "error": "Task not found"}), 404
            cursor.execute("DELETE FROM tasks WHERE id = ?;", (task_id,))
            conn.commit()
        else:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM tasks WHERE id = %s;", (task_id,))
                if not cursor.fetchone():
                    conn.close()
                    return jsonify({"success": False, "error": "Task not found"}), 404
                cursor.execute("DELETE FROM tasks WHERE id = %s;", (task_id,))

        conn.close()
        return jsonify({"success": True, "message": f"Task {task_id} deleted successfully"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to delete task: {str(e)}"}), 500


# Automatically run DB initialization on boot
init_db()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"Starting Flask server on http://127.0.0.1:{port}...")
    app.run(host="0.0.0.0", port=port, debug=True)
