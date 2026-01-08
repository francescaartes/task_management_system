import sqlite3
from config import DB_FILE

class Database:
    def __init__(self):
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    category TEXT NOT NULL,
                    status TEXT NOT NULL,
                    deadline TEXT NOT NULL,
                    description TEXT NOT NULL         
                )
            ''')
            conn.commit()

    def get_all_tasks(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks ORDER BY id")
            return [dict(row) for row in cursor.fetchall()]

    def add_task(self, data):
        with self.get_connection() as conn:
            conn.execute('''
                INSERT INTO tasks (title, category, status, deadline, description)
                VALUES (:title, :category, :status, :deadline, :description)
            ''', data)
            conn.commit()

    def update_task(self, task_id, data):
        with self.get_connection() as conn:
            conn.execute('''
                UPDATE tasks 
                SET title=:title, category=:category, status=:status, 
                    deadline=:deadline, description=:description
                WHERE id=:id
            ''', {**data, 'id': task_id})
            conn.commit()

    def update_status(self, task_id, new_status):
        with self.get_connection() as conn:
            conn.execute("UPDATE tasks SET status=? WHERE id=?", (new_status, task_id))
            conn.commit()

    def delete_task(self, task_id):
        with self.get_connection() as conn:
            conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.commit()