import sqlite3
import bcrypt
from datetime import datetime, timedelta
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

        create_tags = '''
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            );
        '''

        create_task_tags = '''
            CREATE TABLE IF NOT EXISTS task_tags (
                task_id INTEGER,
                tag_id INTEGER,
                PRIMARY KEY (task_id, tag_id),
                FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE,
                FOREIGN KEY(tag_id) REFERENCES tags(id) ON DELETE CASCADE
            );
        '''

        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(create_users)
            cursor.execute(create_tasks)
            cursor.execute(create_tags)
            cursor.execute(create_task_tags)
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
        tags_input = data.pop('tags', '')

        query = '''
            INSERT INTO tasks (user_id, title, category, status, deadline, description)
            VALUES (:user_id, :title, :category, :status, :deadline, :description)
        '''
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, {**data, 'user_id': user_id})

            new_task_id = cursor.lastrowid
            if tags_input:
                self.set_task_tags(conn, new_task_id, tags_input)

            conn.commit()
        finally:
            conn.close()

    def update_task(self, task_id, data):
        tags_input = data.pop('tags', '')

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
            self.set_task_tags(conn, task_id, tags_input)
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
        today = datetime.now().strftime("%Y-%m-%d 23:59") 
        
        # Compare deadline
        query = "SELECT title, deadline FROM tasks WHERE user_id = ? AND deadline <= ? AND status != 'Done'"
        
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, (user_id, today))
            return cursor.fetchall()
        finally:
            conn.close()

    def get_tasks_with_tags(self, user_id):
        query = '''
            SELECT 
                t.id, 
                t.title, 
                t.category, 
                GROUP_CONCAT(tg.name, ', ') as tags,
                t.status, 
                t.deadline,
                t.description
            FROM tasks t
            LEFT JOIN task_tags tt ON t.id = tt.task_id
            LEFT JOIN tags tg ON tt.tag_id = tg.id
            WHERE t.user_id = ?
            GROUP BY t.id
            ORDER BY t.deadline
        '''
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, (user_id,))
            return cursor.fetchall()
        finally:
            conn.close()

    def set_task_tags(self, conn, task_id, tag_string):
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM task_tags WHERE task_id = ?", (task_id,))
        
        if not tag_string: return

        tags = [t.strip() for t in tag_string.split(',') if t.strip()]
        
        for tag_name in tags:
            cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
            res = cursor.fetchone()
            
            if res:
                tag_id = res['id']
            else:
                cursor.execute("INSERT INTO tags (name) VALUES (?)", (tag_name,))
                tag_id = cursor.lastrowid

            cursor.execute("INSERT INTO task_tags (task_id, tag_id) VALUES (?, ?)", (task_id, tag_id))

    def get_filtered_tasks(self, user_id, filters):
        """
        filters: dict -> {'category': 'Work', 'tag': 'urgent', 'timeframe': 'overdue'}
        """
        # Base Query (reusing the complex JOIN logic to get tags)
        sql = '''
            SELECT 
                t.id, t.title, t.category, t.status, t.deadline, t.description,
                GROUP_CONCAT(tg.name, ', ') as tags
            FROM tasks t
            LEFT JOIN task_tags tt ON t.id = tt.task_id
            LEFT JOIN tags tg ON tt.tag_id = tg.id
            WHERE t.user_id = ?
        '''
        params = [user_id]

        # 1. FILTER: Category (Exact Match)
        if filters.get('category') and filters['category'] != 'All Categories':
            sql += " AND t.category = ?"
            params.append(filters['category'])

        # 2. FILTER: Status (Exact Match - mostly for List View)
        if filters.get('status') and filters['status'] != 'All Status':
            sql += " AND t.status = ?"
            params.append(filters['status'])

        # 3. FILTER
        tag_search = filters.get('tag')
        if tag_search:
            # Subquery: Find task_ids that have this tag
            sql += ''' AND t.id IN (
                        SELECT tt.task_id FROM task_tags tt 
                        JOIN tags tg ON tt.tag_id = tg.id 
                        WHERE tg.name LIKE ?
                      )'''
            params.append(f"%{tag_search}%")

        # 4. FILTER: Timeframe (Date Logic)
        timeframe = filters.get('timeframe')
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        if timeframe == 'Overdue':
            sql += " AND t.deadline < ? AND t.status != 'Done'"
            params.append(now_str)
        elif timeframe == 'Due Today':
            # Matches today's date (ignoring time for the start match)
            today_start = datetime.now().strftime("%Y-%m-%d 00:00")
            today_end = datetime.now().strftime("%Y-%m-%d 23:59")
            sql += " AND t.deadline BETWEEN ? AND ?"
            params.extend([today_start, today_end])
        elif timeframe == 'Next 7 Days':
            today_start = datetime.now().strftime("%Y-%m-%d 00:00")
            next_week = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d 23:59")
            sql += " AND t.deadline BETWEEN ? AND ?"
            params.extend([today_start, next_week])

        search_query = filters.get('search')
        if search_query:
            sql += " AND t.title LIKE ?"
            params.append(f"%{search_query}%")

        # Finalize Query
        sql += " GROUP BY t.id ORDER BY t.deadline"
        
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return cursor.fetchall()
        finally:
            conn.close()

    # Helper to populate Category Dropdown
    def get_all_categories(self, user_id):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT category FROM tasks WHERE user_id = ?", (user_id,))
            return [row['category'] for row in cursor.fetchall()]
        finally:
            conn.close()