import sqlite3
import bcrypt
from datetime import datetime, timedelta
import os
from pathlib import Path
import stat

APP_NAME = "TaskFlow"

# Application data directory
app_data = Path(os.getenv("APPDATA")) / APP_NAME
app_data.mkdir(parents=True, exist_ok=True)

# Database file path
DB_FILE = app_data / ".syscache" 

class Database:
    def __init__(self):
        # Initialize database and tables
        self.init_db()

    def get_connection(self):
        # Create and configure a database connection
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
        # Convert query results into dictionaries
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d
    
    def secure_db_file(self):
        # Restrict database file permissions
        if DB_FILE.exists():
            os.chmod(DB_FILE, stat.S_IREAD | stat.S_IWRITE)

    def init_db(self):
        # User accounts table
        create_users = '''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            );
        '''

        # Tasks table
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

        # Tags master table
        create_tags = '''
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            );
        '''

        # Task–tag relationship table
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

    def create_user(self, username, email, password):
        # Create a new user with hashed password
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        query = "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)"
        
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, (username, email, hashed_pw.decode('utf-8')))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            # Duplicate username
            return False
        except Exception as e:
            print(f"Register Error: {e}")
            return False
        finally:
            conn.close()

    def verify_user(self, username, password):
        # Validate user login credentials
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

    def get_user_by_email(self, email):
        # To find a user by email
        query = "SELECT id, username FROM users WHERE email = ?"
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, (email,))
            return cursor.fetchone() # Returns None if not found
        finally:
            conn.close()
    
    def get_all_tasks(self, user_id):
        # Retrieve all tasks for a user
        query = "SELECT * FROM tasks WHERE user_id = ? ORDER BY id"
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, (user_id,))
            return cursor.fetchall()
        finally:
            conn.close()

    def add_task(self, data, user_id):
        # Insert a new task and assign tags
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
        # Update task details and tags
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
        # Change task status only
        query = "UPDATE tasks SET status=? WHERE id=?"
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, (new_status, task_id))
            conn.commit()
        finally:
            conn.close()

    def delete_task(self, task_id):
        # Remove a task
        query = "DELETE FROM tasks WHERE id = ?"
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, (task_id,))
            conn.commit()
        finally:
            conn.close()
    
    def search_tasks(self, user_id, query):
        # Search tasks by text fields
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
        # Update username and/or password
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # Update username and password
            if new_password:
                hashed_pw = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
                cursor.execute(
                    "UPDATE users SET username=?, password_hash=? WHERE id=?",
                    (new_username, hashed_pw.decode('utf-8'), user_id)
                )
            # Update username only
            else:
                cursor.execute(
                    "UPDATE users SET username=? WHERE id=?",
                    (new_username, user_id)
                )
                
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            # Username already exists
            return False
        finally:
            conn.close()

    def get_analytics(self, user_id):
        # Generate task statistics for dashboard
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            today = datetime.now().strftime("%Y-%m-%d")

            cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
            result = cursor.fetchone()
            username = result['username'] if result else "Unknown"

            # Count all tasks
            cursor.execute("SELECT COUNT(*) as total FROM tasks WHERE user_id = ?", (user_id,))
            total_tasks = cursor.fetchone()['total']

            # Count overdue tasks
            cursor.execute(
                "SELECT COUNT(*) as overdue FROM tasks WHERE user_id = ? AND deadline < ? AND status != 'Done'",
                (user_id, today)
            )
            overdue_tasks = cursor.fetchone()['overdue']

            # Count tasks by category and status
            cursor.execute('''
                SELECT category, status, COUNT(*) as count 
                FROM tasks 
                WHERE user_id = ? 
                GROUP BY category, status
            ''', (user_id,))
            
            raw_data = cursor.fetchall()
            
            # Organize results for UI display
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
        # Fetch tasks due today or earlier
        today = datetime.now().strftime("%Y-%m-%d 23:59") 
        
        query = "SELECT title, deadline FROM tasks WHERE user_id = ? AND deadline <= ? AND status != 'Done'"
        
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, (user_id, today))
            return cursor.fetchall()
        finally:
            conn.close()

    def get_tasks_with_tags(self, user_id):
        # Retrieve tasks with their associated tags
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
        # Assign tags to a task
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM task_tags WHERE task_id = ?", (task_id,))
        
        if not tag_string:
            return

        tags = [t.strip() for t in tag_string.split(',') if t.strip()]
        
        for tag_name in tags:
            cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
            res = cursor.fetchone()
            
            if res:
                tag_id = res['id']
            else:
                cursor.execute("INSERT INTO tags (name) VALUES (?)", (tag_name,))
                tag_id = cursor.lastrowid

            cursor.execute(
                "INSERT INTO task_tags (task_id, tag_id) VALUES (?, ?)",
                (task_id, tag_id)
            )

    def get_filtered_tasks(self, user_id, filters):
        """
        Apply category, status, tag, timeframe, and search filters.
        """
        # Base query with tag joins
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

        # Filter by category
        if filters.get('category') and filters['category'] != 'All Categories':
            sql += " AND t.category = ?"
            params.append(filters['category'])

        # Filter by status
        if filters.get('status') and filters['status'] != 'All Status':
            sql += " AND t.status = ?"
            params.append(filters['status'])

        # Filter by tag
        tag_search = filters.get('tag')
        if tag_search:
            sql += ''' AND t.id IN (
                        SELECT tt.task_id FROM task_tags tt 
                        JOIN tags tg ON tt.tag_id = tg.id 
                        WHERE tg.name LIKE ?
                      )'''
            params.append(f"%{tag_search}%")

        # Filter by timeframe
        timeframe = filters.get('timeframe')
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        if timeframe == 'Overdue':
            sql += " AND t.deadline < ? AND t.status != 'Done'"
            params.append(now_str)
        elif timeframe == 'Due Today':
            today_start = datetime.now().strftime("%Y-%m-%d 00:00")
            today_end = datetime.now().strftime("%Y-%m-%d 23:59")
            sql += " AND t.deadline BETWEEN ? AND ?"
            params.extend([today_start, today_end])
        elif timeframe == 'Next 7 Days':
            today_start = datetime.now().strftime("%Y-%m-%d 00:00")
            next_week = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d 23:59")
            sql += " AND t.deadline BETWEEN ? AND ?"
            params.extend([today_start, next_week])

        # Filter by title search
        search_query = filters.get('search')
        if search_query:
            sql += " AND t.title LIKE ?"
            params.append(f"%{search_query}%")

        # Final query
        sql += " GROUP BY t.id ORDER BY t.deadline"
        
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return cursor.fetchall()
        finally:
            conn.close()

    # Retrieve unique task categories
    def get_all_categories(self, user_id):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT DISTINCT category FROM tasks WHERE user_id = ?",
                (user_id,)
            )
            return [row['category'] for row in cursor.fetchall()]
        finally:
            conn.close()
