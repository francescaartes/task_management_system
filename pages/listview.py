import tkinter as tk
from tkinter import ttk, messagebox
from utils.config import COLORS, FONTS
from utils.components import Header, create_input_field

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
        sidebar = tk.Frame(content, bg=COLORS['primary_bg'], width=350, bd=1, relief='ridge')
        sidebar.pack(side='left', fill='y', padx=20)
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

        search_frame = tk.Frame(content, bg=COLORS['primary_bg'], pady=10)
        search_frame.pack(fill='x')

        self.search_var = tk.StringVar()
        
        # Search Entry
        search_entry = tk.Entry(
            search_frame, 
            textvariable=self.search_var, 
            font=FONTS['default'],
            bg=COLORS['secondary_bg'],
            fg=COLORS['primary_txt'],
            insertbackground=COLORS['primary_accent'],
            relief='flat', bd=0, highlightthickness=1,
            highlightbackground=COLORS['primary_accent']
        )
        search_entry.pack(side='left', fill='x', expand=True, padx=(0, 10), ipady=5)
        search_entry.bind('<Return>', self.perform_search) # Bind Enter Key

        # Search Button
        tk.Button(search_frame, text="Search", command=self.perform_search,
                  bg=COLORS['primary_accent'], fg='white', font=FONTS['bold'], width=10
                  ).pack(side='left', padx=(0, 5))

        # Reset Button
        tk.Button(search_frame, text="Reset", command=self.reset_search,
                  bg=COLORS['secondary_bg'], fg=COLORS['primary_txt'], font=FONTS['bold'], width=8
                  ).pack(side='left')

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
            ("Id", 0, 'w'), ("Title", 150, 'w'), ("Category", 100, 'center'),
            ("Status", 100, 'center'), ("Deadline", 100, 'center'), ("Description", 200, 'w') 
        ]

        for col, width, pos in column_config:
            self.tree.column(col, width=width, anchor=pos, stretch=(col!="Id"))
            self.tree.heading(col, text=col if col != "Id" else '', anchor='center')

        self.tree.bind('<<TreeviewSelect>>', self.on_select)

    # Search Logic
    def perform_search(self, event=None):
        query = self.search_var.get().strip()
        if not query:
            self.refresh() # If empty, show all
            return

        # Clear current table
        for item in self.tree.get_children(): 
            self.tree.delete(item)
            
        # Get filtered results from DB
        user_id = self.controller.current_user_id
        results = self.controller.db.search_tasks(user_id, query)
        
        if results:
            for task in results:
                self.tree.insert('', 'end', values=list(task.values()))
        else:
            pass

    def reset_search(self):
        self.search_var.set("")
        self.refresh()

    def refresh(self):
        user_id = self.controller.current_user_id
        for item in self.tree.get_children(): 
            self.tree.delete(item)

        # Standard refresh gets ALL tasks
        for task in self.controller.db.get_all_tasks(user_id):
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
        user_id = self.controller.current_user_id
        try:
            self.controller.db.add_task(self.get_data(), user_id)
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
