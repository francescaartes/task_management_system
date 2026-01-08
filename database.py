import sqlite3
import bcrypt

DB_FILE = 'task_management.db'

class Database:
    def __init__(self):
        self.init_db()

    def get_connection(self):
        try:
            conn = sqlite3.connect(DB_FILE)
            conn.execute("PRAGMA foreign_keys = 1")
            conn.row_factory = self.dict_factory
            return conn
        except Exception as e:
            print(f"Connection Error: {e}")
            raise e

    def dict_factory(self, cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

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