import tkinter as tk
from tkinter import ttk, messagebox
from config import COLORS, FONTS, ADMIN_USER, ADMIN_PASS
from components import Header, create_input_field

class LoginPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLORS['primary_bg'])
        self.controller = controller
        Header(self, controller, show_nav=False).pack(fill='x')
        
        container = tk.Frame(
            self, 
            bg=COLORS['primary_bg'], 
            borderwidth=1, 
            relief='groove',
            padx=20,
            pady=20
        )
        container.place(relx=0.5, rely=0.5, anchor='center')
        
        tk.Label(
            container,
            text='Welcome back',
            font=FONTS['header'],
            bg=COLORS['primary_bg'],
            fg=COLORS['primary_accent'],
            padx=20,
            pady=20
        ).pack(anchor='w')
        
        self.user_var = tk.StringVar()
        self.pass_var = tk.StringVar()
        
        input_frame = tk.Frame(
            container,
            bg=COLORS['primary_bg'],
        )
        input_frame.pack(fill='x', pady=(0, 20), padx=20)
        create_input_field(input_frame, 'Username:', self.user_var, 0, 0, 'entry')
        create_input_field(input_frame, 'Password:', self.pass_var, 1, 0, 'entry', mask=True)

        btn_frame = tk.Frame(
            container,
            bg=COLORS['primary_bg']
        )
        btn_frame.pack(fill='x', pady=(0, 30), padx=20)
        tk.Button(
            btn_frame,
            text='Login',
            command=self.check_login,
            font=FONTS['bold'],
            bg=COLORS['primary_accent'],
            fg=COLORS['secondary_txt']
        ).pack(fill='x', anchor='center')
        self.bind('<Return>', self.check_login)

    def check_login(self, event=None):
        if self.user_var.get() == ADMIN_USER and self.pass_var.get() == ADMIN_PASS:
            self.controller.login_success()
        else:
            messagebox.showerror("Login Error", "Incorrect username or password. Please try again.")

class ListViewPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLORS['primary_bg'])
        self.controller = controller
        Header(self, controller, show_nav=True).pack(fill='x')
        
        self.selected_id = None
        self.setup_ui()
        
    def setup_ui(self):
        content = tk.Frame(self, bg=COLORS['primary_bg'])
        content.pack(side='right', fill='both', expand=True, padx=(0, 20), pady=(0, 20))
        
        # Sidebar
        sidebar = tk.Frame(content, bg=COLORS['primary_bg'], width=350, bd=0, relief='ridge')
        sidebar.pack(side='left', fill='y', padx=20, pady=(0, 20))
        sidebar.pack_propagate(False)
        
        # Inputs
        self.vars = {
            'title': tk.StringVar(), 'category': tk.StringVar(),
            'status': tk.StringVar(), 'deadline': tk.StringVar()
        }
        input_frame = tk.Frame(sidebar, bg=COLORS['primary_bg'], padx=10, pady=10)
        input_frame.pack(fill='x')
        input_frame.grid_columnconfigure(1, weight=1)
        
        create_input_field(input_frame, 'Title:', self.vars['title'], 0, 0, 'entry')
        create_input_field(input_frame, 'Category:', self.vars['category'], 1, 0, 'entry')
        create_input_field(input_frame, 'Status:', self.vars['status'], 2, 0, 'dropdown')
        create_input_field(input_frame, 'Deadline:', self.vars['deadline'], 3, 0, 'date_picker')
        self.description = create_input_field(input_frame, 'Description:', None, 4, 0, 'textarea')

        # Buttons
        btn_frame = tk.Frame(sidebar, bg=COLORS['primary_bg'], pady=10)
        btn_frame.pack(fill='x')
        for text, cmd in [('Add', self.add_task), ('Update', self.update_task), 
                          ('Delete', self.delete_task), ('Clear', self.clear_fields)]:
            if text == 'Clear':
                tk.Button(btn_frame, text=text, command=cmd, font=FONTS['bold'], 
                      bg=COLORS['secondary_bg'], fg=COLORS['primary_accent']).pack(fill='x', padx=15, pady=5)
                continue
            tk.Button(btn_frame, text=text, command=cmd, font=FONTS['bold'], 
                      bg=COLORS['primary_accent'], fg='white').pack(fill='x', padx=15, pady=5)

        # Table
        self.setup_table(content)
        
    def setup_table(self, parent):
        y_tree_scroll = ttk.Scrollbar(parent, orient='vertical')
        y_tree_scroll.pack(side='right', fill='y')
        
        self.tree = ttk.Treeview(
            parent, 
            columns=("Id", "Title", "Category", "Status", "Deadline", "Description"),
            show='headings',
            yscrollcommand=y_tree_scroll.set, 
        )
        self.tree.pack(side='left', fill='both', expand=True)
        
        y_tree_scroll.config(command=self.tree.yview)

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
                self.tree.column(col, width=width, anchor=pos, stretch='no')
                self.tree.heading(col, text='', anchor='center')
            else:
                self.tree.column(col, width=width, anchor=pos)
                self.tree.heading(col, text=col, anchor='center')

        self.tree.bind('<<TreeviewSelect>>', self.on_select)

        def on_mousewheel(event):
            self.tree.yview_scroll(int(-1*(event.delta/120)), "units")

        def bind_scroll(event):
            self.tree.bind_all("<MouseWheel>", on_mousewheel)

        def unbind_scroll(event):
            self.tree.unbind_all("<MouseWheel>")

        self.tree.bind('<Enter>', bind_scroll)
        self.tree.bind('<Leave>', unbind_scroll)

    def refresh(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        for task in self.controller.db.get_all_tasks():
            self.tree.insert('', 'end', values=list(task.values()))

    def on_select(self, event):
        sel = self.tree.selection()
        if not sel: return
        vals = self.tree.item(sel[0], 'values')
        self.selected_id = vals[0]
        self.vars['title'].set(vals[1])
        self.vars['category'].set(vals[2])
        self.vars['status'].set(vals[3])
        self.vars['deadline'].set(vals[4])
        self.description.delete('1.0', tk.END)
        self.description.insert('1.0', vals[5])

    def validate_input(self, inputs):
        if not inputs['title']:
            messagebox.showwarning("Input Error", "Title is required.")
            return False

        if not inputs['category']:
            messagebox.showwarning("Input Error", "Category is required.")
            return False
            
        if not inputs['status']:
            messagebox.showwarning("Input Error", "Status is required.")
            return False
            
        if not inputs['deadline']:
            messagebox.showwarning("Input Error", "Deadline is required.")
            return False
        
        if not inputs['description']:
            messagebox.showwarning("Input Error", "Description is required.")
            return False
        
        return True

    def get_data(self):
        return {k: v.get().strip() for k,v in self.vars.items()} | {'description': self.description.get('1.0', 'end-1c').strip()}

    def add_task(self):
        data = self.get_data()
        validated = self.validate_input(data)

        if not validated:
            return

        if self.selected_id:
            confirm = messagebox.askyesno("Duplicate Task", "Do you want to add this as a NEW task?")
            if not confirm:
                return
            self.selected_id = None

        try:
            self.controller.db.add_task(self.get_data())
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to add task:\n{e}")
            
        self.refresh()
        self.clear_fields()

    def update_task(self):
        data = self.get_data()
        validated = self.validate_input(data)

        if not validated:
            return
        
        if self.selected_id:
            try:
                self.controller.db.update_task(self.selected_id, self.get_data())
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to update task:\n{e}")
            self.refresh()
            self.clear_fields()
        else:
            messagebox.showwarning(
                "Selection Required",
                "Please select a task first by clicking on it in the table."
            )
            return


    def delete_task(self):
        if not self.selected_id:
            return
        
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this task?\nThis action cannot be undone."):
            try:
                self.controller.db.delete_task(self.selected_id)
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to delete task:\n{e}")
            self.refresh()
            self.clear_fields()

    def clear_fields(self):
        for v in self.vars.values(): v.set('')
        self.description.delete('1.0', tk.END)
        self.selected_id = None

class KanbanPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLORS['secondary_bg'])
        self.controller = controller
        Header(self, controller, show_nav=True).pack(fill='x')
        
        # Main container
        self.board = tk.Frame(self, bg=COLORS['secondary_bg'])
        self.board.pack(fill='both', expand=True, padx=20, pady=20)
        
        self.columns = {}
        self.drag_data = {"ghost": None, "task_id": None, "offset_x": 0, "offset_y": 0}

    def refresh(self):
        for widget in self.board.winfo_children(): widget.destroy()
        self.columns = {} 
        
        tasks = self.controller.db.get_all_tasks()
        
        # Rebuild columns
        for i, status in enumerate(['To Do', 'In Progress', 'Done']):
            outer_frame, inner_frame = self.create_column_widget(
                self.board, status, i
            )
            
            self.columns[status] = outer_frame

            current_tasks = [t for t in tasks if t['status'] == status]
            for task in current_tasks:
                self.create_card(inner_frame, task)

    def create_column_widget(self, parent, title, index):
        outer_frame = tk.Frame(parent, bg=COLORS['primary_bg'], bd=1, relief='solid')
        outer_frame.place(relx=index/3, rely=0, relwidth=0.32, relheight=1)

        # Header
        tk.Label(outer_frame, text=title.upper(), font=FONTS['bold'], 
                 bg=COLORS['primary_accent'], fg='white', pady=5).pack(fill='x')

        # Canvas & Scrollbar Container
        container = tk.Frame(outer_frame, bg=COLORS['primary_bg'])
        container.pack(fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(container, orient="vertical")
        scrollbar.pack(side="right", fill="y")
        
        canvas = tk.Canvas(container, bg=COLORS['primary_bg'], bd=0, 
                           highlightthickness=0, yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        
        scrollbar.config(command=canvas.yview)

        # Inner Frame 
        inner_frame = tk.Frame(canvas, bg=COLORS['primary_bg'])
        canvas_window = canvas.create_window((0, 0), window=inner_frame, anchor="nw")

        # Scrolling & Resizing
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            
        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)
            
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        inner_frame.bind("<Configure>", on_frame_configure)
        canvas.bind("<Configure>", on_canvas_configure)
        
        # Bind mousewheel
        inner_frame.bind('<Enter>', lambda e: canvas.bind_all("<MouseWheel>", on_mousewheel))
        inner_frame.bind('<Leave>', lambda e: canvas.unbind_all("<MouseWheel>"))

        return outer_frame, inner_frame

    def create_card(self, parent, task):
        card = tk.Frame(parent, bg='white', bd=1, relief='raised', padx=10, pady=10)
        card.pack(fill='x', padx=5, pady=5)
        
        tk.Label(card, text=task['title'], font=FONTS['bold'], bg='white', fg=COLORS['primary_accent']).pack(anchor='w')
        tk.Label(card, text=task['category'], font=FONTS['small'], bg='white', fg='gray').pack(anchor='w')
        tk.Label(card, text=f"Due: {task['deadline']}", font=FONTS['small'], bg='white', fg=COLORS['primary_accent']).pack(anchor='w')

        # Drag Bindings
        card.bind("<Button-1>", lambda e, tid=task['id']: self.drag_start(e, card, tid, task['title']))
        for child in card.winfo_children():
            child.bind("<Button-1>", lambda e, tid=task['id']: self.drag_start(e, card, tid, task['title']))

    def drag_start(self, event, card, task_id, title):
        self.drag_data["task_id"] = task_id
        self.drag_data["offset_x"] = event.x_root - card.winfo_rootx()
        self.drag_data["offset_y"] = event.y_root - card.winfo_rooty()
        
        self.drag_data["ghost"] = tk.Frame(self, bg='white', bd=2, relief='solid', padx=10, pady=10)
        tk.Label(self.drag_data["ghost"], text=title, bg='white', fg=COLORS['primary_accent'], font=FONTS['bold']).pack()
        self.drag_data["ghost"].place(x=event.x_root - self.winfo_rootx(), y=event.y_root - self.winfo_rooty())
        
        self.controller.bind("<B1-Motion>", self.drag_motion)
        self.controller.bind("<ButtonRelease-1>", self.drag_release)

    def drag_motion(self, event):
        if self.drag_data["ghost"]:
            self.drag_data["ghost"].place(x=event.x_root - self.winfo_rootx() - self.drag_data['offset_x'],
                                          y=event.y_root - self.winfo_rooty() - self.drag_data['offset_y'])

    def drag_release(self, event):
        if self.drag_data["ghost"]:
            self.drag_data["ghost"].destroy()
            self.drag_data["ghost"] = None
            self.controller.unbind("<B1-Motion>")
            self.controller.unbind("<ButtonRelease-1>")
            
            x, y = event.x_root, event.y_root
            for status, col in self.columns.items():
                if col.winfo_rootx() <= x <= col.winfo_rootx() + col.winfo_width():
                    self.controller.db.update_status(self.drag_data["task_id"], status)
                    self.refresh()
                    break