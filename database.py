import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt
from config import DB_HOST, DB_NAME, DB_PASS, DB_PORT, DB_USER

class Database:
    def __init__(self):
        self.init_db()

    def get_connection(self):
        try:
            return psycopg2.connect(
                host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS, port=DB_PORT
            )
        except Exception as e:
            print(f"Connection Error: {e}")
            raise e

    def init_db(self):
        # Users Table
        create_users = '''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            );
        '''

        # Tasks Table
        create_tasks = '''
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                status TEXT NOT NULL,
                deadline TEXT NOT NULL,
                description TEXT NOT NULL,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE
            );
        '''

        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(create_users)
                cursor.execute(create_tasks)
                conn.commit()

    def create_user(self, username, password):
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        query = "INSERT INTO users (username, password_hash) VALUES (%s, %s)"
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (username, hashed_pw.decode('utf-8')))
                    conn.commit()
            return True
        except psycopg2.IntegrityError:
            # Username taken
            return False
        except Exception as e:
            print(f"Register Error: {e}")
            return False

    def verify_user(self, username, password):
        query = "SELECT id, password_hash FROM users WHERE username = %s"
        
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (username,))
                user = cursor.fetchone()
                
                if user:
                    stored_hash = user['password_hash'].encode('utf-8')
                    if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
                        return user['id']
        return None
    
    def get_all_tasks(self, user_id):
        query = "SELECT * FROM tasks WHERE user_id = %s ORDER BY id"
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (user_id,))
                return cursor.fetchall()

    def add_task(self, data, user_id):
        query = '''
            INSERT INTO tasks (user_id, title, category, status, deadline, description)
            VALUES (%(user_id)s, %(title)s, %(category)s, %(status)s, %(deadline)s, %(description)s)
        '''
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, {**data, 'user_id': user_id})
                conn.commit()

    def update_task(self, task_id, data):
        query = '''
            UPDATE tasks 
            SET title=%(title)s, category=%(category)s, status=%(status)s, 
                deadline=%(deadline)s, description=%(description)s
            WHERE id=%(id)s
        '''
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, {**data, 'id': task_id})
                conn.commit()

    def update_status(self, task_id, new_status):
        query = "UPDATE tasks SET status=%s WHERE id=%s"
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (new_status, task_id))
                conn.commit()

    def delete_task(self, task_id):
        query = "DELETE FROM tasks WHERE id = %s"
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (task_id,))
                conn.commit()