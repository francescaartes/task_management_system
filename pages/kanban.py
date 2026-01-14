import tkinter as tk
from tkinter import ttk, messagebox
from utils.config import COLORS, FONTS
from utils.components import Header, create_input_field, FilterBar


class TaskModal(tk.Toplevel):
    """Modal window for adding or editing a single task."""

    def __init__(self, parent, task=None, on_save=None):
        super().__init__(parent)
        self.task = task
        self.on_save = on_save

        # --- Window Setup ---
        title = "View/Edit Task" if task else "Add New Task"
        self.title(title)
        window_width = 480
        window_height = 480

        # Center window on screen
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        center_x = int(screen_width / 2 - window_width / 2)
        center_y = int(screen_height / 2 - window_height / 2)
        self.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')

        self.configure(bg=COLORS['primary_bg'])
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()  # Make modal (block parent)

        # --- Tk Variables ---
        self.title_var = tk.StringVar()
        self.cat_var = tk.StringVar()
        self.tags_var = tk.StringVar()
        self.status_var = tk.StringVar(value="To Do")
        self.date_var = tk.StringVar()

        # --- Main Container ---
        self.container = tk.Frame(self, bg=COLORS['primary_bg'])
        self.container.pack(fill='both', expand=True, padx=20, pady=20)
        self.container.columnconfigure(1, weight=1)  # Allow inputs to expand

        self._build_ui()

        # Populate fields if editing existing task
        if self.task:
            self._populate_data()

    def _build_ui(self):
        """Build all input fields and buttons in the modal."""
        # Input fields
        create_input_field(self.container, "Title:", self.title_var, 0, 0, 'entry')
        self.cat_cb = create_input_field(self.container, "Category:", self.cat_var, 1, 0, 'entry')
        create_input_field(self.container, "Tags (#):", self.tags_var, 2, 0, 'entry')
        create_input_field(self.container, "Status:", self.status_var, 3, 0, 'dropdown')
        create_input_field(self.container, "Deadline:", self.date_var, 4, 0, 'date_picker')
        self.desc_text = create_input_field(self.container, "Description:", None, 5, 0, 'textarea')

        # Action buttons
        btn_frame = tk.Frame(self.container, bg=COLORS['primary_bg'])
        btn_frame.grid(row=7, column=0, columnspan=2, pady=25, sticky='e')

        tk.Button(btn_frame, text="Save", bg=COLORS['primary_accent'], fg=COLORS['primary_bg'], font=FONTS['bold'],
                  command=self.save_data).pack(side='right', padx=5)

        tk.Button(btn_frame, text="Cancel", bg=COLORS['secondary_bg'], fg=COLORS['primary_txt'], font=FONTS['bold'],
                  command=self.destroy).pack(side='right', padx=5)

    def _populate_data(self):
        """Populate modal fields with existing task information."""
        self.title_var.set(self.task.get('title', ''))
        self.cat_var.set(self.task.get('category', ''))
        self.tags_var.set(self.task.get('tags', ''))
        self.status_var.set(self.task.get('status', 'To Do'))
        self.date_var.set(self.task.get('deadline', ''))

        self.desc_text.delete("1.0", tk.END)
        self.desc_text.insert("1.0", self.task.get('description', ''))

    def save_data(self):
        """Validate and save modal data, then call on_save callback."""
        data = {
            "title": self.title_var.get(),
            "category": self.cat_var.get(),
            "tags": self.tags_var.get(),
            "status": self.status_var.get(),
            "deadline": self.date_var.get(),
            "description": self.desc_text.get("1.0", "end-1c").strip()
        }

        # Simple validation
        if not data["title"]:
            messagebox.showerror("Error", "Title is required")
            return

        # Call callback if provided
        if self.on_save:
            self.on_save(data)

        # Close modal
        self.destroy()


class KanbanPage(tk.Frame):
    """Kanban board view for tasks with drag-and-drop support."""

    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLORS['primary_bg'])
        self.controller = controller
        Header(self, controller, show_nav=True).pack(fill='x')

        # --- Action bar / controls ---
        action_bar = tk.Frame(self, bg=COLORS['primary_bg'])
        action_bar.pack(fill='x', padx=20, pady=0)

        # Add Task Button
        tk.Button(action_bar, text="➕\nAdd Task", bg=COLORS['primary_accent'], fg=COLORS['primary_bg'],
                  font=FONTS['bold'],
                  command=self.open_add_modal).pack(side='left', fill='both')

        # Filter bar
        self.filter_bar = FilterBar(action_bar, self.controller, on_filter_command=self.refresh)
        self.filter_bar.pack(fill='x', padx=(20, 0))

        # Kanban board container
        self.board = tk.Frame(self, bg=COLORS['primary_bg'])
        self.board.pack(fill='both', expand=True, padx=(20, 0), pady=20)

        # Internal state for columns and drag-and-drop
        self.columns = {}
        self.drag_data = {"ghost": None, "task_id": None, "offset_x": 0, "offset_y": 0}

    def tkraise(self, *args, **kwargs):
        """Override tkraise to refresh board whenever page is shown."""
        super().tkraise(*args, **kwargs)
        self.refresh()

    def refresh(self, filters=None):
        """Reload all tasks (filtered if provided) and redraw Kanban columns."""
        # Refresh filter options
        if hasattr(self, 'filter_bar'):
            self.filter_bar.refresh_options()

        # Clear current board
        for widget in self.board.winfo_children():
            widget.destroy()
        self.columns = {}

        user_id = self.controller.current_user_id

        # Fetch tasks
        tasks = self.controller.db.get_filtered_tasks(user_id, filters) if filters else self.controller.db.get_tasks_with_tags(user_id)

        # Draw columns and add tasks
        for i, status in enumerate(['To Do', 'In Progress', 'Done']):
            outer_frame, inner_frame = self.create_column_widget(self.board, status, i)
            self.columns[status] = outer_frame

            # Filter tasks for this column
            current_tasks = [t for t in tasks if t['status'] == status]
            for task in current_tasks:
                self.create_card(inner_frame, task)

    # --- Modal / CRUD Helpers ---
    def open_add_modal(self):
        """Open modal to add a new task."""
        def save_new(data):
            self.controller.db.add_task(data, self.controller.current_user_id)
            self.refresh()
        TaskModal(self, task=None, on_save=save_new)

    def open_details_modal(self, task):
        """Open modal to view/edit an existing task."""
        def save_edit(data):
            self.controller.db.update_task(task['id'], data)
            self.refresh()
        TaskModal(self, task=task, on_save=save_edit)

    def delete_task_action(self, task_id):
        """Delete a task after confirmation."""
        if messagebox.askyesno("Delete", "Are you sure you want to delete this task?"):
            self.controller.db.delete_task(task_id)
            self.refresh()

    # --- Column / Card Creation ---
    def create_column_widget(self, parent, title, index):
        """Create a single Kanban column with scrollable area."""
        outer_frame = tk.Frame(parent, bg=COLORS['primary_bg'], bd=1, relief='solid')
        outer_frame.place(relx=index/3, rely=0, relwidth=0.32, relheight=1)

        tk.Label(outer_frame, text=title.upper(), font=FONTS['bold'],
                 bg=COLORS['primary_accent'], fg='white', pady=5).pack(fill='x')

        container = tk.Frame(outer_frame, bg=COLORS['primary_bg'])
        container.pack(fill='both', expand=True)

        # Scrollable canvas
        scrollbar = ttk.Scrollbar(container, orient="vertical")
        scrollbar.pack(side="right", fill="y")

        canvas = tk.Canvas(container, bg=COLORS['primary_bg'], bd=0,
                           highlightthickness=0, yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=canvas.yview)

        inner_frame = tk.Frame(canvas, bg=COLORS['primary_bg'])
        canvas_window = canvas.create_window((0, 0), window=inner_frame, anchor="nw")

        # Auto-update scrollregion
        def on_configure(event): canvas.configure(scrollregion=canvas.bbox("all"))
        inner_frame.bind("<Configure>", on_configure)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))

        return outer_frame, inner_frame

    def create_card(self, parent, task):
        """Create a single task card with drag & drop and right-click menu."""
        card = tk.Frame(parent, bg='white', bd=1, relief='raised', padx=10, pady=10)
        card.pack(fill='x', padx=5, pady=5)

        # Display tags
        self.display_tags(card, task.get('tags', ''))

        # Task info labels
        tk.Label(card, text=task['title'],
                 font=FONTS['bold'], bg='white', fg=COLORS['primary_accent'],
                 wraplength=250, justify='left').pack(anchor='w')
        tk.Label(card, text=task['category'], font=FONTS['small'], bg='white', fg='gray').pack(anchor='w')
        tk.Label(card, text=f"Due: {task['deadline']}", font=FONTS['small'], bg='white', fg=COLORS['primary_accent']).pack(anchor='w')

        # Context menu for right-click
        context_menu = tk.Menu(self, tearoff=0)
        context_menu.add_command(label="View Details", command=lambda: self.open_details_modal(task))
        context_menu.add_separator()
        context_menu.add_command(label="Delete", command=lambda: self.delete_task_action(task['id']))

        def do_popup(event):
            try: context_menu.tk_popup(event.x_root, event.y_root)
            finally: context_menu.grab_release()

        # Bind left-click for drag
        card.bind("<Button-1>", lambda e, tid=task['id']: self.drag_start(e, card, tid, task['title']))
        # Bind right-click for context menu
        if self.tk.call('tk', 'windowingsystem') == 'aqua':
            card.bind("<Button-2>", do_popup)
        else:
            card.bind("<Button-3>", do_popup)

        # Apply same bindings to all children (labels)
        for child in card.winfo_children():
            child.bind("<Button-1>", lambda e, tid=task['id']: self.drag_start(e, card, tid, task['title']))
            if self.tk.call('tk', 'windowingsystem') == 'aqua':
                child.bind("<Button-2>", do_popup)
            else:
                child.bind("<Button-3>", do_popup)
            child.bind("<Double-Button-1>", lambda e: self.open_details_modal(task))

    def display_tags(self, parent, tags_str):
        """Display comma-separated tags as chips on a card."""
        if tags_str:
            tag_frame = tk.Frame(parent, bg='white')
            tag_frame.pack(anchor='w', fill='x', pady=(0, 6))

            for tag_text in tags_str.split(','):
                tag_text = tag_text.strip()
                if tag_text:
                    chip = tk.Label(
                        tag_frame,
                        text=tag_text,
                        font=FONTS['small'],
                        bg=COLORS['secondary_bg'],
                        fg=COLORS['primary_txt'],
                        padx=6, pady=2
                    )
                    chip.pack(side='left', padx=(0, 5))

    # --- Drag & Drop Handlers ---
    def drag_start(self, event, card, task_id, title):
        """Initialize drag operation with ghost widget."""
        self.drag_data["task_id"] = task_id
        self.drag_data["offset_x"] = event.x_root - card.winfo_rootx()
        self.drag_data["offset_y"] = event.y_root - card.winfo_rooty()

        # Create ghost for visual feedback
        self.drag_data["ghost"] = tk.Frame(self, bg='white', bd=2, relief='solid', padx=10, pady=10)
        tk.Label(self.drag_data["ghost"], text=title, bg='white', fg=COLORS['primary_accent'], font=FONTS['bold']).pack()
        self.drag_data["ghost"].place(x=event.x_root - self.winfo_rootx(), y=event.y_root - self.winfo_rooty())

        # Bind motion and release events globally
        self.controller.bind("<B1-Motion>", self.drag_motion)
        self.controller.bind("<ButtonRelease-1>", self.drag_release)

    def drag_motion(self, event):
        """Move ghost widget with mouse while dragging."""
        if self.drag_data["ghost"]:
            self.drag_data["ghost"].place(
                x=event.x_root - self.winfo_rootx() - self.drag_data['offset_x'],
                y=event.y_root - self.winfo_rooty() - self.drag_data['offset_y']
            )

    def drag_release(self, event):
        """Finalize drag, check which column it was dropped into, update task status."""
        if self.drag_data["ghost"]:
            self.drag_data["ghost"].destroy()
            self.drag_data["ghost"] = None

            self.controller.unbind("<B1-Motion>")
            self.controller.unbind("<ButtonRelease-1>")

            x, y = event.x_root, event.y_root
            for status, col in self.columns.items():
                if (col.winfo_rootx() <= x <= col.winfo_rootx() + col.winfo_width() and
                    col.winfo_rooty() <= y <= col.winfo_rooty() + col.winfo_height()):
                    # Update task status in DB
                    self.controller.db.update_status(self.drag_data["task_id"], status)
                    self.refresh()
                    break
