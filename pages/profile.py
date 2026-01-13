import tkinter as tk
from tkinter import ttk
from utils.config import COLORS, FONTS
from utils.components import Header, create_input_field

class ProfilePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLORS['primary_bg'])
        self.controller = controller
        Header(self, controller, show_nav=True).pack(fill='x')

        self.data_matrix = {}

        # Container
        container = tk.Frame(self, bg=COLORS['primary_bg'], padx=40, pady=20)
        container.pack(fill='both', expand=True)

        # Header + Overview
        header_frame = tk.Frame(container, bg=COLORS['primary_bg'])
        header_frame.pack(fill='x', pady=(0, 30))
        
        # User Icon
        tk.Label(header_frame, text="👤", font=("Arial", 40), bg=COLORS['primary_bg'], fg=COLORS['primary_accent']).pack(side='left', padx=(0, 20))
        
        # Stats Text
        username = getattr(self.controller, 'current_user', 'User')
        self.username_lbl = tk.Label(header_frame, text=username, font=FONTS['header'], bg=COLORS['primary_bg'], fg=COLORS['primary_accent'])
        self.username_lbl.pack(anchor='w')
        
        self.total_lbl = tk.Label(header_frame, text="Total Tasks: 0", font=FONTS['default'], bg=COLORS['primary_bg'], fg='gray')
        self.total_lbl.pack(anchor='w')
        
        # Overdue badge
        self.overdue_lbl = tk.Label(header_frame, text="0 Overdue Task/s", font=FONTS['bold'], bg=COLORS['primary_bg'], fg=COLORS['primary_accent'])
        self.overdue_lbl.pack(anchor='w', pady=(5, 0))

        # Analytics area
        control_frame = tk.Frame(container, bg=COLORS['primary_bg'], padx=20, pady=20, bd=1, relief='groove')
        control_frame.pack(fill='both', expand=True)
        
        tk.Label(control_frame, text="Tasks Analytics", font=FONTS['header'], bg=COLORS['primary_bg'], fg=COLORS['primary_accent']).pack(anchor='w', pady=(0, 15))
        
        # Dropdown for Category Selection
        self.cat_var = tk.StringVar()
        self.cat_dropdown = ttk.Combobox(control_frame, textvariable=self.cat_var, state='readonly', font=FONTS['default'])
        self.cat_dropdown.pack(fill='x', pady=(0, 20))
        self.cat_dropdown.bind("<<ComboboxSelected>>", self.update_charts)

        # Chart Container
        self.chart_frame = tk.Frame(control_frame, bg=COLORS['primary_bg'])
        self.chart_frame.pack(fill='both', expand=True)
        
        # Initial Placeholder
        tk.Label(self.chart_frame, text="Select a category above to view analytics.", bg=COLORS['primary_bg'], fg='gray').pack(pady=20)

    def tkraise(self, *args, **kwargs):
        super().tkraise(*args, **kwargs)
        self.refresh_data()

    def refresh_data(self):
        user_id = self.controller.current_user_id
        username = getattr(self.controller, 'current_user', 'User') 
        self.username_lbl.config(text=username)
        
        if not user_id: return

        # Fetch Complex Data from DB
        analytics = self.controller.db.get_analytics(user_id) 
        
        self.data_matrix = analytics['matrix']
        self.total_lbl.config(text=f"Total Tasks: {analytics['total_tasks']}")
        
        # Container for the totals
        all_stats = {'total': 0, 'To Do': 0, 'In Progress': 0, 'Done': 0}
        
        # Loop through every category and sum their stats
        for cat_data in self.data_matrix.values():
            all_stats['total'] += cat_data.get('total', 0)
            all_stats['To Do'] += cat_data.get('To Do', 0)
            all_stats['In Progress'] += cat_data.get('In Progress', 0)
            all_stats['Done'] += cat_data.get('Done', 0)
            
        self.data_matrix['All Categories'] = all_stats

        # Update Overdue Warning
        od = analytics['overdue_tasks']
        if od > 0:
            self.overdue_lbl.config(text=f"⚠ {od} Tasks Overdue!", fg='#ff4444')
        else:
            self.overdue_lbl.config(text="✓ No Overdue Tasks", fg='#00C851')

        # Populate Dropdown
        categories = [k for k in self.data_matrix.keys() if k != 'All Categories']
        categories.sort() 
        categories.insert(0, 'All Categories')
        
        self.cat_dropdown['values'] = categories
        
        if categories:
            self.cat_dropdown.current(0) # Select "All Categories" automatically
            self.update_charts() 
        else:
            self.cat_var.set("No Categories Found")

    def update_charts(self, event=None):
        # Clear previous charts
        for widget in self.chart_frame.winfo_children(): widget.destroy()
        
        category = self.cat_var.get()
        if category not in self.data_matrix: return

        data = self.data_matrix[category]
        total = data['total']
        
        if total == 0: return

        # Helper to draw a bar
        def draw_bar(label, value, count):
            percent = (count / total) * 100
            
            # Row Container
            row = tk.Frame(self.chart_frame, bg=COLORS['primary_bg'], pady=5)
            row.pack(fill='x')
            
            # Text Labels
            lbl_frame = tk.Frame(row, bg=COLORS['primary_bg'])
            lbl_frame.pack(fill='x')
            tk.Label(lbl_frame, text=label, font=FONTS['bold'], bg=COLORS['primary_bg'], fg=COLORS['primary_accent']).pack(side='left')
            tk.Label(lbl_frame, text=f"{int(percent)}% ({count})", font=FONTS['small'], bg=COLORS['primary_bg'], fg=COLORS['primary_accent']).pack(side='right')

            # Progress Bar (Bottom)
            canvas = tk.Canvas(row, height=10, bg=COLORS['primary_bg'], bd=0, highlightthickness=0)
            canvas.pack(fill='x', pady=0)
            
            # Draw filled portion
            bar_width = (percent / 100) * self.chart_frame.winfo_width() 
            
            # Frame as a bar
            progress_bg = tk.Frame(row, height=20, bg=COLORS['primary_bg'], bd=1, relief='solid') # track
            progress_bg.pack(fill='x', pady=0)
            
            fill_bar = tk.Frame(progress_bg, height=20, bg=COLORS['primary_accent'])
            fill_bar.place(relx=0, rely=0, relheight=1, relwidth=(percent/100))

        # DRAW THE 3 BARS
        todo = data.get('To Do', 0)
        draw_bar("To Do", todo, todo)

        inp = data.get('In Progress', 0)
        draw_bar("In Progress", inp, inp)

        done = data.get('Done', 0)
        draw_bar("Done", done, done)
