import sqlite3
import bcrypt
from datetime import datetime
import os
from pathlib import Path
import stat

APP_NAME = "TaskFlow"

app_data = Path(os.getenv("APPDATA")) / APP_NAME
app_data.mkdir(parents=True, exist_ok=True)

DB_FILE = app_data / ".syscache" 
class Database:
    def __init__(self):
        self.init_db()

    def get_connection(self):
        try:
            conn = sqlite3.connect(DB_FILE, timeout=10)
            conn.row_factory = self.dict_factory

            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")
            conn.execute("PRAGMA temp_store = MEMORY")
            conn.execute("PRAGMA secure_delete = ON")

            return conn
        except Exception as e:
            print(f"Connection Error: {e}")
            raise

    def dict_factory(self, cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d
    
    def secure_db_file(self):
        if DB_FILE.exists():
            os.chmod(DB_FILE, stat.S_IREAD | stat.S_IWRITE)

    def init_db(self):
        # Users Table
        create_users = '''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            );
        '''

        # Tasks Table
        create_tasks = '''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                status TEXT NOT NULL,
                deadline TEXT NOT NULL,
                description TEXT NOT NULL,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE
            );
        '''

        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(create_users)
            cursor.execute(create_tasks)
            conn.commit()
        finally:
            conn.close()

        self.secure_db_file()

    def create_user(self, username, password):
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        query = "INSERT INTO users (username, password_hash) VALUES (?, ?)"
        
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, (username, hashed_pw.decode('utf-8')))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            # Username taken
            return False
        except Exception as e:
            print(f"Register Error: {e}")
            return False
        finally:
            conn.close()

    def verify_user(self, username, password):
        query = "SELECT id, password_hash FROM users WHERE username = ?"
        
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, (username,))
            user = cursor.fetchone()
            
            if user:
                stored_hash = user['password_hash'].encode('utf-8')
                if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
                    return user['id']
            return None
        finally:
            conn.close()
    
    def get_all_tasks(self, user_id):
        query = "SELECT * FROM tasks WHERE user_id = ? ORDER BY id"
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, (user_id,))
            return cursor.fetchall()
        finally:
            conn.close()

    def add_task(self, data, user_id):
        query = '''
            INSERT INTO tasks (user_id, title, category, status, deadline, description)
            VALUES (:user_id, :title, :category, :status, :deadline, :description)
        '''
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, {**data, 'user_id': user_id})
            conn.commit()
        finally:
            conn.close()

    def update_task(self, task_id, data):
        query = '''
            UPDATE tasks 
            SET title=:title, category=:category, status=:status, 
                deadline=:deadline, description=:description
            WHERE id=:id
        '''
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, {**data, 'id': task_id})
            conn.commit()
        finally:
            conn.close()

    def update_status(self, task_id, new_status):
        query = "UPDATE tasks SET status=? WHERE id=?"
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, (new_status, task_id))
            conn.commit()
        finally:
            conn.close()

    def delete_task(self, task_id):
        query = "DELETE FROM tasks WHERE id = ?"
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, (task_id,))
            conn.commit()
        finally:
            conn.close()
    
    def search_tasks(self, user_id, query):
        search_term = f"%{query}%"
        
        sql = '''
            SELECT * FROM tasks 
            WHERE user_id = ? 
            AND (title LIKE ? OR category LIKE ? OR description LIKE ?)
            ORDER BY id
        '''
        
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(sql, (user_id, search_term, search_term, search_term))
            return cursor.fetchall()
        finally:
            conn.close()

    def update_credentials(self, user_id, new_username, new_password):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # Udate BOTH or just Password
            if new_password:
                hashed_pw = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
                cursor.execute(
                    "UPDATE users SET username=?, password_hash=? WHERE id=?",
                    (new_username, hashed_pw.decode('utf-8'), user_id)
                )
            
            # Only update Username
            else:
                cursor.execute(
                    "UPDATE users SET username=? WHERE id=?",
                    (new_username, user_id)
                )
                
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False # Username taken
        finally:
            conn.close()

    def get_analytics(self, user_id):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            today = datetime.now().strftime("%Y-%m-%d")

            cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
            result = cursor.fetchone()
            username = result['username'] if result else "Unknown"

            # Total Overview
            cursor.execute("SELECT COUNT(*) as total FROM tasks WHERE user_id = ?", (user_id,))
            total_tasks = cursor.fetchone()['total']

            # Overdue Count
            cursor.execute("SELECT COUNT(*) as overdue FROM tasks WHERE user_id = ? AND deadline < ? AND status != 'Done'", (user_id, today))
            overdue_tasks = cursor.fetchone()['overdue']

            # Group by Category AND Status
            cursor.execute('''
                SELECT category, status, COUNT(*) as count 
                FROM tasks 
                WHERE user_id = ? 
                GROUP BY category, status
            ''', (user_id,))
            
            raw_data = cursor.fetchall()
            
            # Process into a structured dictionary for the UI
            matrix = {}
            for row in raw_data:
                cat = row['category']
                status = row['status']
                count = row['count']
                
                if cat not in matrix:
                    matrix[cat] = {'total': 0, 'Done': 0, 'In Progress': 0, 'To Do': 0}
                
                if status not in matrix[cat]:
                    matrix[cat][status] = 0
                
                matrix[cat][status] = count
                matrix[cat]['total'] += count

            return {
                'username': username,
                'total_tasks': total_tasks,
                'overdue_tasks': overdue_tasks,
                'matrix': matrix
            }
        finally:
            conn.close()

    def get_due_today(self, user_id):
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        
        query = "SELECT title, deadline FROM tasks WHERE user_id = ? AND deadline <= ? AND status != 'Done'"
        
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, (user_id, today))
            return cursor.fetchall()
        finally:
            conn.close()