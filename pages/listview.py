import tkinter as tk
from tkinter import ttk, messagebox
from utils.config import COLORS, FONTS
from utils.components import Header, create_input_field, FilterBar


class ListViewPage(tk.Frame):
    """Main task list view with sidebar, filters, and table."""

    def __init__(self, parent, controller):
        """Initialize list view page UI."""
        super().__init__(parent, bg=COLORS['primary_bg'])
        self.controller = controller
        Header(self, controller, show_nav=True).pack(fill='x')

        self.selected_id = None
        self.setup_ui()

    def setup_ui(self):
        """Set up sidebar, input fields, buttons, filters, and table."""
        content = tk.Frame(self, bg=COLORS['primary_bg'])
        content.pack(side='right', fill='both', expand=True, padx=(0, 20), pady=(0, 20))

        # Sidebar
        sidebar = tk.Frame(content, bg=COLORS['primary_bg'], width=350, bd=1, relief='ridge')
        sidebar.pack(side='left', fill='y', padx=20)
        sidebar.pack_propagate(False)

        # Input fields
        self.vars = {
            'title': tk.StringVar(),
            'category': tk.StringVar(),
            'tags': tk.StringVar(),
            'status': tk.StringVar(),
            'deadline': tk.StringVar()
        }

        input_frame = tk.Frame(sidebar, bg=COLORS['primary_bg'], padx=10, pady=10)
        input_frame.pack(fill='x')
        input_frame.grid_columnconfigure(1, weight=1)

        create_input_field(input_frame, 'Title:', self.vars['title'], 0, 0, 'entry')
        create_input_field(input_frame, 'Category:', self.vars['category'], 1, 0, 'entry')
        create_input_field(input_frame, 'Tags (#):', self.vars['tags'], 2, 0, 'entry')
        create_input_field(input_frame, 'Status:', self.vars['status'], 3, 0, 'dropdown')
        create_input_field(input_frame, 'Deadline:', self.vars['deadline'], 4, 0, 'date_picker')
        self.description = create_input_field(input_frame, 'Description:', None, 5, 0, 'textarea')

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

        # Filter bar
        filter_frame = tk.Frame(content, bg=COLORS['primary_bg'])
        filter_frame.pack(fill='x')
        self.filter_bar = FilterBar(filter_frame, self.controller, on_filter_command=self.refresh)
        self.filter_bar.pack(fill='x')

        # Table
        self.setup_table(content)

    def setup_table(self, parent):
        """Create treeview table with scrollbars."""
        y_tree_scroll = ttk.Scrollbar(parent, orient='vertical')
        x_tree_scroll = ttk.Scrollbar(parent, orient="horizontal")
        y_tree_scroll.pack(side='right', fill='y')
        x_tree_scroll.pack(side='bottom', fill='x')

        self.tree = ttk.Treeview(
            parent,
            columns=("Id", "Title", "Category", "Status", "Deadline", "Description", "Tags"),
            show='headings',
            yscrollcommand=y_tree_scroll.set,
            xscrollcommand=x_tree_scroll.set,
        )
        self.tree.pack(side='left', fill='both', expand=True)
        y_tree_scroll.config(command=self.tree.yview)
        x_tree_scroll.config(command=self.tree.xview)

        column_config = [
            ("Id", 0, 'w'), ("Title", 150, 'w'), ("Category", 100, 'center'),
            ("Status", 100, 'center'), ("Deadline", 100, 'center'),
            ("Description", 200, 'w'), ("Tags", 100, 'w')
        ]
        for col, width, pos in column_config:
            self.tree.column(col, width=width, anchor=pos, stretch=(col != "Id"))
            self.tree.heading(col, text=col if col != "Id" else '', anchor='center')

        self.tree.bind('<<TreeviewSelect>>', self.on_select)

    # --- Search / Refresh Methods ---
    def perform_search(self, event=None):
        """Search tasks by query and refresh table."""
        query = self.search_var.get().strip()
        if not query:
            self.refresh()
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        user_id = self.controller.current_user_id
        results = self.controller.db.search_tasks(user_id, query)

        if results:
            for task in results:
                self.tree.insert('', 'end', values=list(task.values()))

    def reset_search(self):
        """Clear search field and refresh."""
        self.search_var.set("")
        self.refresh()

    def refresh(self, filters=None):
        """Reload tasks table with optional filters."""
        if hasattr(self, 'filter_bar'):
            self.filter_bar.refresh_options()

        for item in self.tree.get_children():
            self.tree.delete(item)

        user_id = self.controller.current_user_id
        tasks = self.controller.db.get_filtered_tasks(user_id, filters) if filters else self.controller.db.get_tasks_with_tags(user_id)

        for task in tasks:
            values = [task['id'], task['title'], task['category'], task['status'],
                      task['deadline'], task['description'], task.get('tags', '')]
            self.tree.insert('', 'end', values=values)

    def on_select(self, event):
        """Populate sidebar fields when a task is selected."""
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0], 'values')
        self.selected_id = vals[0]
        self.vars['title'].set(vals[1])
        self.vars['category'].set(vals[2])
        self.vars['tags'].set(vals[6])
        self.vars['status'].set(vals[3])
        self.vars['deadline'].set(vals[4])
        self.description.delete('1.0', tk.END)
        self.description.insert('1.0', vals[5])

    def validate_input(self, inputs):
        """Ensure required fields are filled."""
        required_fields = ['title', 'category', 'status', 'deadline', 'description']
        for field in required_fields:
            if not inputs.get(field):
                messagebox.showwarning("Input Error", f"{field.capitalize()} is required.")
                return False
        return True

    def get_data(self):
        """Retrieve current input data from sidebar fields."""
        return {k: v.get().strip() for k, v in self.vars.items()} | {'description': self.description.get('1.0', 'end-1c').strip()}

    # --- CRUD Operations ---
    def add_task(self):
        """Add a new task to the database."""
        data = self.get_data()
        if not self.validate_input(data):
            return

        if self.selected_id:
            confirm = messagebox.askyesno("Duplicate Task", "Do you want to add this as a NEW task?")
            if not confirm:
                return
            self.selected_id = None

        user_id = self.controller.current_user_id
        try:
            self.controller.db.add_task(data, user_id)
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to add task:\n{e}")

        self.refresh()
        self.clear_fields()

    def update_task(self):
        """Update the selected task in the database."""
        data = self.get_data()
        if not self.validate_input(data):
            return

        if self.selected_id:
            try:
                self.controller.db.update_task(self.selected_id, data)
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to update task:\n{e}")
            self.refresh()
            self.clear_fields()
        else:
            messagebox.showwarning("Selection Required", "Please select a task first by clicking on it in the table.")

    def delete_task(self):
        """Delete the selected task from the database."""
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
        """Clear all sidebar input fields."""
        for v in self.vars.values():
            v.set('')
        self.description.delete('1.0', tk.END)
        self.selected_id = None
