import tkinter as tk
from tkinter import ttk
from tkcalendar import DateEntry
from datetime import datetime
from config import COLORS, FONTS

class Header(tk.Frame):
    def __init__(self, parent, controller, show_nav=True):
        super().__init__(parent, bg=COLORS['primary_bg'], height=60, bd=1, relief='groove')
        self.controller = controller
        self.pack(fill='x', pady=(0, 20))
        
        try:
            logo_img = tk.PhotoImage(file="icon.png")
        except:
            logo_img = None
        self.logo_img = logo_img 
        
        tk.Label(self, image=logo_img, bg=COLORS['primary_bg']).pack(side='left', padx=(20, 10), pady=10) 
        tk.Label(self, text='TaskFlow', font=FONTS['header'], 
                 bg=COLORS['primary_bg'], fg=COLORS['primary_accent']).pack(side='left')

        if show_nav:
            self.create_nav_buttons()

    def create_nav_buttons(self):
        nav_frame = tk.Frame(self, bg=COLORS['primary_bg'])
        nav_frame.pack(side='right', padx=20)

        buttons = [
            ("Logout", self.controller.logout),
            ("Kanban", lambda: self.controller.show_view("KanbanPage")),
            ("List View", lambda: self.controller.show_view("ListViewPage"))
        ]

        for text, command in buttons:
            btn = tk.Button(nav_frame, text=text, command=command,
                            bg=COLORS['primary_bg'], fg=COLORS['primary_accent'],
                            font=FONTS['bold'], relief='flat', bd=0,
                            activebackground=COLORS['secondary_bg'])
            btn.pack(side='right', padx=10)

class ScrollableFrame(tk.Frame):
    def __init__(self, parent, bg_color="#FFFFFF", *args, **kwargs):
        super().__init__(parent, bg=bg_color, *args, **kwargs)

        # 1. The Canvas
        self.canvas = tk.Canvas(self, bg=bg_color, bd=0, highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)

        # 2. The Scrollbar
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollbar.pack(side="right", fill="y")
        
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # 3. The Internal Frame (This is where your widgets go!)
        self.scrollable_content = tk.Frame(self.canvas, bg=bg_color)
        
        # Add the internal frame to the canvas window
        self.canvas_window = self.canvas.create_window(
            (0, 0), 
            window=self.scrollable_content, 
            anchor="nw"
        )

        # 4. Bindings for Resizing
        self.scrollable_content.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        
        # 5. Mousewheel Scrolling (Optional but recommended)
        self.bind_mouse_scroll()

    def _on_frame_configure(self, event):
        """Reset the scroll region to encompass the inner frame"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        """Force the inner frame to match the canvas width"""
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def bind_mouse_scroll(self):
        # Bind mousewheel when mouse enters/leaves the frame
        self.scrollable_content.bind('<Enter>', self._bound_to_mousewheel)
        self.scrollable_content.bind('<Leave>', self._unbound_to_mousewheel)

    def _bound_to_mousewheel(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbound_to_mousewheel(self, event):
        self.canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

def create_input_field(parent, label_text, var, row, col, input_type, mask=False):
        label = tk.Label(
            parent,
            text=label_text,
            font=FONTS['bold'],
            bg=COLORS['primary_bg'],
            fg=COLORS['primary_accent'],
            anchor='w'
        )
        label.grid(row=row, column=col, sticky='w', padx=(10, 5), pady=5)

        match input_type:
            case 'entry':
                entry = tk.Entry(
                    parent,
                    textvariable=var,
                    font=FONTS['default'],
                    bg=COLORS['secondary_bg'],
                    fg=COLORS['primary_txt'],
                    insertbackground=COLORS['primary_accent'],
                    show='*' if mask else '',
                )
                entry.grid(row=row, column=col+1, sticky='ew', padx=(0, 10), pady=5, ipady=3)
                return entry
            
            case 'textarea':
                text_container = tk.Frame(parent, bg=COLORS['primary_bg'])
                text_container.grid(row=row + 1, column=0, columnspan=2, sticky='ew', padx=10, pady=(0, 10))
                
                scrollbar = ttk.Scrollbar(text_container)
                scrollbar.pack(side='right', fill='y')
                
                textarea = tk.Text(
                    text_container,
                    wrap=tk.WORD,
                    height=8,
                    font=FONTS['default'],
                    bg=COLORS['secondary_bg'],
                    fg=COLORS['primary_txt'],
                    insertbackground=COLORS['primary_accent'],
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
                    font=FONTS['default'],
                    values=status_options,
                    state='readonly',
                )
                combobox.grid(row=row, column=col+1, sticky='ew', padx=(0, 10), pady=5, ipady=5)
                return combobox

            case 'date_picker':
                cal = DateEntry(
                    parent, 
                    width=12, 
                    background=COLORS['primary_accent'],
                    foreground='white', 
                    borderwidth=2, 
                    date_pattern='yyyy-mm-dd',
                    font=FONTS['default']
                )
                cal.grid(row=row, column=col+1, sticky='ew', padx=(0, 10), pady=5, ipady=3)

                def on_date_select(event):
                    var.set(cal.get_date())
                
                cal.bind("<<DateEntrySelected>>", on_date_select)

                def update_calendar(*args):
                    try:
                        if not cal.winfo_exists():
                            return
                        
                        date_str = var.get()
                        if date_str:
                            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                            cal.set_date(date_obj)
                    except (ValueError, tk.TclError):
                        pass 

                trace_id = var.trace_add("write", update_calendar)

                def on_destroy(event):
                    try:
                        var.trace_remove("write", trace_id)
                    except:
                        pass
                
                cal.bind("<Destroy>", on_destroy)

                return cal

            case _:
                return None