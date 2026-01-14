import tkinter as tk
from tkinter import ttk, messagebox
from utils.config import COLORS, FONTS
from utils.components import Header, create_input_field 

class TaskModal(tk.Toplevel):
    def __init__(self, parent, task=None, on_save=None):
        super().__init__(parent)
        self.task = task
        self.on_save = on_save
        
        # Window Setup
        title = "View/Edit Task" if task else "Add New Task"
        self.title(title)
        window_width = 480
        window_height = 480
        
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        center_x = int(screen_width/2 - window_width / 2)
        center_y = int(screen_height/2 - window_height / 2)

        self.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        self.configure(bg=COLORS['primary_bg'])
        self.resizable(False, False)
        
        self.transient(parent)
        self.grab_set()
        
        # Variables
        self.title_var = tk.StringVar()
        self.cat_var = tk.StringVar()
        self.status_var = tk.StringVar(value="To Do")
        self.date_var = tk.StringVar()
        
        # Main Container
        self.container = tk.Frame(self, bg=COLORS['primary_bg'])
        self.container.pack(fill='both', expand=True, padx=20, pady=20)
        self.container.columnconfigure(1, weight=1)

        self._build_ui()
        
        if self.task:
            self._populate_data()

    def _build_ui(self):
        # Fields
        create_input_field(self.container, "Title:", self.title_var, 0, 0, 'entry')
        self.cat_cb = create_input_field(self.container, "Category:", self.cat_var, 1, 0, 'entry')
        create_input_field(self.container, "Status:", self.status_var, 2, 0, 'dropdown')
        create_input_field(self.container, "Deadline:", self.date_var, 3, 0, 'date_picker')
        self.desc_text = create_input_field(self.container, "Description:", None, 4, 0, 'textarea')

        # Buttons
        btn_frame = tk.Frame(self.container, bg=COLORS['primary_bg'])
        btn_frame.grid(row=6, column=0, columnspan=2, pady=25, sticky='e')

        tk.Button(btn_frame, text="Save", bg=COLORS['primary_accent'], fg='white', font=FONTS['bold'],
                  command=self.save_data).pack(side='right', padx=5)
        
        tk.Button(btn_frame, text="Cancel", bg='gray', fg='white', font=FONTS['bold'],
                  command=self.destroy).pack(side='right', padx=5)

    def _populate_data(self):
        """Populate fields with existing task data"""
        self.title_var.set(self.task.get('title', ''))
        self.cat_var.set(self.task.get('category', ''))
        self.status_var.set(self.task.get('status', 'To Do'))
        self.date_var.set(self.task.get('deadline', ''))
        
        self.desc_text.delete("1.0", tk.END)
        self.desc_text.insert("1.0", self.task.get('description', ''))

    def save_data(self):
        data = {
            "title": self.title_var.get(),
            "category": self.cat_var.get(),
            "status": self.status_var.get(),
            "deadline": self.date_var.get(),
            "description": self.desc_text.get("1.0", "end-1c").strip()
        }
        
        if not data["title"]:
            messagebox.showerror("Error", "Title is required")
            return

        if self.on_save:
            self.on_save(data)
        self.destroy()

class KanbanPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLORS['secondary_bg'])
        self.controller = controller
        Header(self, controller, show_nav=True).pack(fill='x')
        
        # Controls Area
        action_bar = tk.Frame(self, bg=COLORS['secondary_bg'])
        action_bar.pack(fill='x', padx=20, pady=0)
        
        # Add Task Button
        tk.Button(action_bar, text="+ Add Task", bg=COLORS['primary_accent'], fg='white', 
                  font=FONTS['bold'], padx=15, pady=5, bd=0,
                  command=self.open_add_modal).pack(side='left')
        
        # Board Container
        self.board = tk.Frame(self, bg=COLORS['secondary_bg'])
        self.board.pack(fill='both', expand=True, padx=(20, 0), pady=20)
        
        self.columns = {}
        self.drag_data = {"ghost": None, "task_id": None, "offset_x": 0, "offset_y": 0}

    def refresh(self):
        """Re-fetches tasks and redraws the board"""
        for widget in self.board.winfo_children(): widget.destroy()
        self.columns = {} 
        
        user_id = self.controller.current_user_id
        tasks = self.controller.db.get_all_tasks(user_id)
        
        for i, status in enumerate(['To Do', 'In Progress', 'Done']):
            outer_frame, inner_frame = self.create_column_widget(self.board, status, i)
            self.columns[status] = outer_frame

            current_tasks = [t for t in tasks if t['status'] == status]
            for task in current_tasks:
                self.create_card(inner_frame, task)

    def open_add_modal(self):
        def save_new(data):
            self.controller.db.add_task(data, self.controller.current_user_id)
            self.refresh()
        TaskModal(self, task=None, on_save=save_new)

    def open_details_modal(self, task):
        """Opens modal for View/Edit details"""
        def save_edit(data):
            self.controller.db.update_task(task['id'], data)
            self.refresh()
        TaskModal(self, task=task, on_save=save_edit)

    def delete_task_action(self, task_id):
        if messagebox.askyesno("Delete", "Are you sure you want to delete this task?"):
            self.controller.db.delete_task(task_id)
            self.refresh()

    def create_column_widget(self, parent, title, index):
        outer_frame = tk.Frame(parent, bg=COLORS['primary_bg'], bd=1, relief='solid')
        outer_frame.place(relx=index/3, rely=0, relwidth=0.32, relheight=1)

        tk.Label(outer_frame, text=title.upper(), font=FONTS['bold'], 
                 bg=COLORS['primary_accent'], fg='white', pady=5).pack(fill='x')

        container = tk.Frame(outer_frame, bg=COLORS['primary_bg'])
        container.pack(fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(container, orient="vertical")
        scrollbar.pack(side="right", fill="y")
        
        canvas = tk.Canvas(container, bg=COLORS['primary_bg'], bd=0, 
                           highlightthickness=0, yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=canvas.yview)

        inner_frame = tk.Frame(canvas, bg=COLORS['primary_bg'])
        canvas_window = canvas.create_window((0, 0), window=inner_frame, anchor="nw")

        def on_configure(event): canvas.configure(scrollregion=canvas.bbox("all"))
        inner_frame.bind("<Configure>", on_configure)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))

        return outer_frame, inner_frame

    def create_card(self, parent, task):
        card = tk.Frame(parent, bg='white', bd=1, relief='raised', padx=10, pady=10)
        card.pack(fill='x', padx=5, pady=5)
        
        tk.Label(
            card, text=task['title'], 
            font=FONTS['bold'], 
            bg='white', fg=COLORS['primary_accent'],
            wraplength=250,
            justify='left'
        ).pack(anchor='w')
        tk.Label(card, text=task['category'], font=FONTS['small'], bg='white', fg='gray').pack(anchor='w')
        tk.Label(card, text=f"Due: {task['deadline']}", font=FONTS['small'], bg='white', fg=COLORS['primary_accent']).pack(anchor='w')

        # Context Menu - Right Click
        context_menu = tk.Menu(self, tearoff=0)
        context_menu.add_command(label="View Details", command=lambda: self.open_details_modal(task))
        context_menu.add_separator()
        context_menu.add_command(label="Delete", command=lambda: self.delete_task_action(task['id']))

        def do_popup(event):
            try: context_menu.tk_popup(event.x_root, event.y_root)
            finally: context_menu.grab_release()

        # Left Click Drag
        card.bind("<Button-1>", lambda e, tid=task['id']: self.drag_start(e, card, tid, task['title']))
        
        # Right Click
        if self.tk.call('tk', 'windowingsystem') == 'aqua':
            card.bind("<Button-2>", do_popup)
        else:
            card.bind("<Button-3>", do_popup)

        for child in card.winfo_children():
            child.bind("<Button-1>", lambda e, tid=task['id']: self.drag_start(e, card, tid, task['title']))
            if self.tk.call('tk', 'windowingsystem') == 'aqua':
                child.bind("<Button-2>", do_popup)
            else:
                child.bind("<Button-3>", do_popup)
            child.bind("<Double-Button-1>", lambda e: self.open_details_modal(task))    

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
                if (col.winfo_rootx() <= x <= col.winfo_rootx() + col.winfo_width() and 
                    col.winfo_rooty() <= y <= col.winfo_rooty() + col.winfo_height()):
                    self.controller.db.update_status(self.drag_data["task_id"], status)
                    self.refresh()
                    break