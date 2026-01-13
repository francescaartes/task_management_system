import tkinter as tk
from tkinter import ttk
from utils.config import COLORS, FONTS
from utils.components import Header, create_input_field

class KanbanPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLORS['secondary_bg'])
        self.controller = controller
        Header(self, controller, show_nav=True).pack(fill='x')
        
        # Main container
        self.board = tk.Frame(self, bg=COLORS['secondary_bg'])
        self.board.pack(fill='both', expand=True, padx=(20, 0), pady=20)
        
        self.columns = {}
        self.drag_data = {"ghost": None, "task_id": None, "offset_x": 0, "offset_y": 0}

    def refresh(self):
        for widget in self.board.winfo_children(): widget.destroy()
        self.columns = {} 
        
        user_id = self.controller.current_user_id
        tasks = self.controller.db.get_all_tasks(user_id)
        
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
