import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime

DB_FILE = 'task_management.db'
class TaskManagementSystem:
    def __init__(self, root):
        self.root = root
        self.root.title('Task Management System')
        self.root.geometry('1100x700')

        self.colors = {
            'primary_bg': "#F8F8FF",
            'secondary_bg': "#E0E0E8",
            'primary_txt': "#1A1A1A",
            'secondary_txt': "#EEEEEE",
            'primary_accent': '#2B3A7E',
        }
        self.font = ('Verdana', 12) 
        self.font_bold = ('Verdana', 12, 'bold') 
        self.root.config(bg=self.colors['primary_bg'])

        self.title_var = tk.StringVar()
        self.status_var = tk.StringVar()
        self.deadline_var = tk.StringVar()
        self.category_var = tk.StringVar()
        self.description_var = None

        self.initialize_styles()
        
        self.USERNAME = 'admin'
        self.PASSWORD = 'admin'
        
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.login = False
        
        self.selected_id = None
        
        self.header()
        self.login_page()

    def login_page(self):
        self.login_frame = tk.Frame(
            self.root, 
            bg=self.colors['primary_bg'], 
            borderwidth=1, 
            relief='groove',
            padx=20,
            pady=20
        )
        self.login_frame.place(anchor='center', relx=0.5, rely=0.5)
        
        login_label = tk.Label(
            self.login_frame,
            text='Welcome back',
            font=('Verdana', 20, 'bold'),
            bg=self.colors['primary_bg'],
            fg=self.colors['primary_accent'],
            padx=20,
            pady=20
        )
        login_label.pack(anchor='w')
        
        input_frame = tk.Frame(
            self.login_frame,
            bg=self.colors['primary_bg'],
        )
        input_frame.pack(fill='x', pady=(0, 20), padx=20)
        self.create_input_field(input_frame, 'Username:', self.username_var, 0, 0, 'entry')
        self.create_input_field(input_frame, 'Password:', self.password_var, 1, 0, 'entry', mask=True)
        
        btn_frame = tk.Frame(
            self.login_frame,
            bg=self.colors['primary_bg']
        )
        btn_frame.pack(fill='x', pady=(0, 30), padx=20)
        login_btn = tk.Button(
            btn_frame,
            text='Login',
            command=self.check_login,
            font=self.font_bold,
            bg=self.colors['primary_accent'],
            fg=self.colors['secondary_txt']
        )
        login_btn.pack(fill='x', anchor='center')
        self.root.bind('<Return>', self.check_login)
        
    def check_login(self, event=None):
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()
        
        if not username or not password:
            return
        
        if username == self.USERNAME and password == self.PASSWORD:
            self.login_frame.destroy()
            self.root.unbind('<Return>')
            self.main_page()
            self.login = True
        else:
            messagebox.showerror("Login Error", "Incorrect username or password. Please try again.")
            self.login = False
    
    def header(self):
        header_frame = tk.Frame(
            self.root, 
            bg=self.colors['primary_bg'], 
            height=60,
            borderwidth=1,
            relief='groove'
        )
        header_frame.pack(fill='x', pady=(0, 20))
        try:
            logo_img = tk.PhotoImage(file="icon.png")
        except:
            logo_img = None

        header_frame.logo_img = logo_img 
        
        image_label = tk.Label(
            header_frame, 
            image=logo_img,
            bg=self.colors['primary_bg']
        )
        image_label.pack(side='left', padx=(20, 10), pady=10) 

        header_label = tk.Label(
            header_frame, 
            text='TaskFlow', 
            font=('Verdana', 20, 'bold'), 
            bg=self.colors['primary_bg'],
            fg=self.colors['primary_accent'],
            anchor='w'
        )
        header_label.pack(side='left', fill='y', expand=False)

    def main_page(self):
        self.root.protocol('WM_DELETE_WINDOW', self.on_close)

        sidebar_frame = tk.Frame(
            self.root,
            bg=self.colors['primary_bg'],
            width=350,
            borderwidth=1,
            relief='ridge'
        )
        sidebar_frame.pack(side='left', fill='y', padx=20, pady=(0, 20)) 
        sidebar_frame.pack_propagate(False)

        input_frame = tk.Frame(sidebar_frame, bg=self.colors['primary_bg'], padx=10, pady=10)
        input_frame.pack(fill='x')
        
        input_frame.grid_columnconfigure(1, weight=1) 

        self.create_input_field(input_frame, 'Title:', self.title_var, 0, 0, 'entry')
        self.create_input_field(input_frame, 'Category:', self.category_var, 1, 0, 'entry')
        self.create_input_field(input_frame, 'Status:', self.status_var, 2, 0, 'dropdown')
        self.create_input_field(input_frame, 'Deadline:', self.deadline_var, 3, 0, 'entry')
        self.description_var = self.create_input_field(input_frame, 'Description:', None, 4, 0, 'textarea')

        button_frame = tk.Frame(sidebar_frame, bg=self.colors['primary_bg'], pady=10, padx=10)
        button_frame.pack(fill='x')

        button_config = [
            ('Add Task', self.add_task),
            ('Update Task', self.update_task),
            ('Delete Task', self.delete_task),
            ('Clear Fields', self.clear_fields)
        ]

        for text, cmd in button_config:
            bg_color = self.colors['secondary_bg'] if text == 'Clear Fields' else self.colors['primary_accent']
            fg_color = self.colors['primary_txt'] if text == 'Clear Fields' else self.colors['secondary_txt']
            font_style = self.font if text == 'Clear Fields' else self.font_bold
            
            tk.Button(
                button_frame,
                text=text,
                command=cmd,
                bg=bg_color,
                fg=fg_color,
                font=font_style,
            ).pack(fill='x', padx=5, pady=5)

        table_frame = tk.Frame(self.root, bg=self.colors['primary_bg'])
        table_frame.pack(fill='both', expand=True, padx=(0,20), pady=(0, 20))

        self.create_table(table_frame)
        self.initialize_database()   

    def create_input_field(self, parent, label_text, var, row, col, input_type, mask=False):
        label = tk.Label(
            parent,
            text=label_text,
            font=self.font_bold,
            bg=self.colors['primary_bg'],
            fg=self.colors['primary_accent'],
            anchor='w'
        )
        label.grid(row=row, column=col, sticky='w', padx=(10, 5), pady=5)

        match input_type:
            case 'entry':
                entry = tk.Entry(
                    parent,
                    textvariable=var,
                    font=self.font,
                    bg=self.colors['secondary_bg'],
                    fg=self.colors['primary_txt'],
                    insertbackground=self.colors['primary_accent'],
                    show='*' if mask else '',
                )
                entry.grid(row=row, column=col+1, sticky='ew', padx=(0, 10), pady=5, ipady=3)
                return entry
            
            case 'textarea':
                text_container = tk.Frame(parent, bg=self.colors['primary_bg'])
                text_container.grid(row=row + 1, column=0, columnspan=2, sticky='ew', padx=10, pady=(0, 10))
                
                scrollbar = ttk.Scrollbar(text_container)
                scrollbar.pack(side='right', fill='y')
                
                textarea = tk.Text(
                    text_container,
                    wrap=tk.WORD,
                    height=8,
                    font=self.font,
                    bg=self.colors['secondary_bg'],
                    fg=self.colors['primary_txt'],
                    insertbackground=self.colors['primary_accent'],
                    yscrollcommand=scrollbar.set,
                    padx=5, pady=5
                )
                textarea.pack(side='left', fill='both', expand=True)
                scrollbar.config(command=textarea.yview)
                return textarea
            
            case 'dropdown':
                status_options = ['To Do', 'In Progress', 'Done']

                combobox = ttk.Combobox(
                    parent, 
                    textvariable=var,
                    font=self.font,
                    values=status_options,
                    state='readonly',
                )
                combobox.grid(row=row, column=col+1, sticky='ew', padx=(0, 10), pady=5, ipady=5)
                return combobox
            
            case _:
                return None
    
    def create_table(self, parent):
        tree_frame = tk.Frame(parent)
        tree_frame.pack(fill='both', expand=True)

        # x_tree_scroll = ttk.Scrollbar(tree_frame, orient='horizontal')
        # x_tree_scroll.pack(side='bottom', fill='x')

        y_tree_scroll = ttk.Scrollbar(tree_frame, orient='vertical')
        y_tree_scroll.pack(side='right', fill='y')
        
        self.task_table = ttk.Treeview(
            tree_frame, 
            columns=("Id", "Title", "Category", "Status", "Deadline", "Description"),
            show='headings',
            yscrollcommand=y_tree_scroll.set, 
            # xscrollcommand=x_tree_scroll.set,
        )
        self.task_table.pack(side='left', fill='both', expand=True)
        
        y_tree_scroll.config(command=self.task_table.yview)
        # x_tree_scroll.config(command=self.task_table.xview)

        column_config = [
            ("Id", 0, 'w'),
            ("Title", 150, 'w'),
            ("Category", 100, 'center'),
            ("Status", 100, 'center'),
            ("Deadline", 100, 'center'),
            ("Description", 200, 'w') 
        ]

        for col, width, pos in column_config:
            if col == "Id":
                self.task_table.column(col, width=width, anchor=pos, stretch='no')
                self.task_table.heading(col, text='', anchor='center')
            else:
                self.task_table.column(col, width=width, anchor=pos)
                self.task_table.heading(col, text=col, anchor='center')

        self.task_table.bind('<<TreeviewSelect>>', self.on_tree_select)

    def on_tree_select(self, event):
        selection = self.task_table.selection()
        if not selection:
            return
        
        item = selection[0]
        values = self.task_table.item(item, 'values')

        self.selected_id = values[0]
        self.title_var.set(values[1])
        self.category_var.set(values[2])
        self.status_var.set(values[3])
        self.deadline_var.set(values[4])

        self.description_var.delete("1.0", 'end-1c')
        self.description_var.insert("1.0", values[5])

    def initialize_database(self):
        try:
            self.conn = sqlite3.connect(DB_FILE)
            self.conn.row_factory = sqlite3.Row
        except sqlite3.Error  as e:
            messagebox.showerror("Database Error", f"Failed to connect to database:\n{e}")

        if not self.conn:
            return False
        
        try:
            self.cursor = self.conn.cursor()
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    category TEXT NOT NULL,
                    status TEXT NOT NULL,
                    deadline TEXT NOT NULL,
                    description TEXT NOT NULL         
                )
            ''')
            self.conn.commit()
            self.refresh_table()
            return True
        except sqlite3.Error as e:
            messagebox.showerror("Databse Error", f"Failed to initialize database:\n{e}")
            return False
    
    def refresh_table(self):
        try:
            for item in self.task_table.get_children():
                self.task_table.delete(item)
            
            self.cursor.execute("SELECT * FROM tasks ORDER BY id")
            rows = self.cursor.fetchall()

            for row in rows:
                self.task_table.insert('', 'end', values=(
                    row['id'],
                    row['title'],
                    row['category'],
                    row['status'],
                    row['deadline'],
                    row['description']
                ))
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Failed to load tasks:\n{e}")
    
    def validate_input(self, inputs):
        _, _, _, deadline, _ = inputs

        if not all(inputs):
            messagebox.showwarning("Validation Error", "All fields are required.")
            return False
        
        try:
            datetime.strptime(deadline, '%Y-%m-%d')
            return True
        except ValueError:
            messagebox.showwarning(
                "Validation Error",
                "Deadline must be in format YYYY-MM-DD\nExample: 2025-11-14"
            )
            return False
        
    def add_task(self):
        title = self.title_var.get().strip()
        category = self.category_var.get().strip()
        status = self.status_var.get().strip()
        deadline = self.deadline_var.get().strip()
        description = self.description_var.get('1.0', 'end-1c').strip()

        validated = self.validate_input((title, category, status, deadline, description))

        if validated:
            try:
                self.cursor.execute('''
                    INSERT INTO tasks (title, category, status, deadline, description)
                    VALUES (?, ?, ?, ?, ?)
                ''', (title, category, status, deadline, description))
                
                self.conn.commit()
                
                messagebox.showinfo("Success", f"Task '{title}' is added successfully.")
                
                self.clear_fields()
                self.refresh_table()
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to add student:\n{e}")
            
    def update_task(self):
        if not self.selected_id:
            messagebox.showwarning(
                "Selection Required",
                "Please select a task first by clicking on it in the table."
            )
            return
        
        title = self.title_var.get().strip()
        category = self.category_var.get().strip()
        status = self.status_var.get().strip()
        deadline = self.deadline_var.get().strip()
        description = self.description_var.get('1.0', 'end-1c').strip()

        validated = self.validate_input((title, category, status, deadline, description))

        if validated:
            try:
                self.cursor.execute('''
                    UPDATE tasks 
                    SET title = ?, category = ?, status = ?, deadline = ?, description = ?
                    WHERE id = ?
                ''', (title, category, status, deadline, description, self.selected_id))

                messagebox.showinfo("Success", f"Task '{title}' is updated successfully.")

                self.conn.commit()
                self.refresh_table()
                self.clear_fields()
            except sqlite3.Error as e:
                messagebox.showerror("Database Error", f"Failed to update task:\n{e}")

    def delete_task(self):
        if not self.selected_id:
            messagebox.showwarning(
                "Selection Required",
                "Please select a task first by clicking on it in the table."
            )
            return
        
        response = messagebox.askyesno(
            "Confirm Delete",
            "Are you sure you want to delete this task?\nThis action cannot be undone."
        )

        if not response:
            return
        
        try:
            self.cursor.execute("DELETE FROM tasks WHERE id = ?", (self.selected_id,))
            self.conn.commit()

            messagebox.showinfo("Success", f"Task '{self.title_var.get().strip()}' is deleted successfully.")

            self.clear_fields()
            self.refresh_table()

        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to delete task:\n{e}")

    def clear_fields(self):
        self.title_var.set("")
        self.status_var.set("")
        self.deadline_var.set("")
        self.category_var.set("")
        self.description_var.delete("1.0", "end")
        self.selected_id = None

        for item in self.task_table.selection():
            self.task_table.selection_remove(item)
            
    def on_close(self):
        if self.conn:
            self.conn.commit()
            self.conn.close()
        self.root.destroy()

    def initialize_styles(self):
        """Initializes and configures all custom ttk styles."""
        style = ttk.Style()
        style.theme_use('default')

        # --- Treeview Style ---
        style.configure(
            "Treeview",
            background=self.colors['primary_bg'],
            foreground=self.colors['primary_txt'],
            fieldbackground=self.colors['primary_bg'],
            font=self.font,
            rowheight=25
        )
        style.map("Treeview", background=[("selected", self.colors['primary_accent'])])
        style.configure(
            "Treeview.Heading",
            background=self.colors['secondary_bg'],
            foreground=self.colors['primary_accent'],
            font=self.font_bold,
            padding=5
        )

        # --- Combobox Style (Windows-compatible) ---
        self.root.option_add('*TCombobox*Listbox.background', self.colors['secondary_bg'])
        self.root.option_add('*TCombobox*Listbox.foreground', self.colors['primary_txt'])
        self.root.option_add('*TCombobox*Listbox.selectBackground', self.colors['primary_accent'])
        self.root.option_add('*TCombobox*Listbox.selectForeground', self.colors['secondary_txt'])

        style.map('TCombobox',
            fieldbackground=[('readonly', self.colors['secondary_bg'])],
            selectbackground=[('readonly', self.colors['secondary_bg'])],
            selectforeground=[('readonly', self.colors['primary_txt'])]
        )
        style.configure('TCombobox',
            background=self.colors['secondary_bg'],
            foreground=self.colors['primary_txt'],
            arrowcolor=self.colors['primary_txt'],
            fieldbackground=self.colors['secondary_bg']
        )

if __name__ == "__main__":
    window = tk.Tk()
    app = TaskManagementSystem(window)
    window.mainloop()
