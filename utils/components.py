import tkinter as tk
from tkinter import ttk
from tkcalendar import DateEntry
from datetime import datetime
import sys
import os
from utils.config import COLORS, FONTS

class Header(tk.Frame):
    def __init__(self, parent, controller, show_nav=True):
        super().__init__(parent, bg=COLORS['primary_bg'], height=60, bd=1, relief='groove')
        self.controller = controller
        self.pack(fill='x', pady=(0, 20))
        
        logo_img = self.resource_path("assets/icon.png")
        try:
            logo_img = tk.PhotoImage(file=logo_img)
        except:
            logo_img = None
        self.logo_img = logo_img 
        
        tk.Label(self, image=logo_img, bg=COLORS['primary_bg']).pack(side='left', padx=(20, 10), pady=10) 
        tk.Label(self, text='TaskFlow', font=FONTS['header'], 
                 bg=COLORS['primary_bg'], fg=COLORS['primary_accent']).pack(side='left')

        user_path = self.resource_path("assets/user.png")
        try:
            self.user_img = tk.PhotoImage(file=user_path)
        except:
            self.user_img = None

        if show_nav:
            self.create_nav_buttons()

    def resource_path(self, relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

    def create_nav_buttons(self):
        nav_frame = tk.Frame(self, bg=COLORS['primary_bg'])
        nav_frame.pack(side='right', padx=20)

        if self.user_img:
            self.user_btn = tk.Button(nav_frame, image=self.user_img, 
                                      bg=COLORS['primary_bg'], bd=0, 
                                      activebackground=COLORS['primary_bg'],
                                      cursor='hand2')
        else:
            # Fallback if image missing
            self.user_btn = tk.Button(nav_frame, text="👤 ", font=("Arial", 16),
                                      bg=COLORS['primary_bg'], fg=COLORS['primary_accent'], bd=0,
                                      activebackground=COLORS['primary_bg'],
                                      cursor='hand2')
            
        self.user_btn.pack(side='right', padx=(10, 0))
        
        # Bind Left Click to show menu
        self.user_btn.bind("<Button-1>", self.show_user_menu)

        buttons = [
            ("Kanban", lambda: self.controller.show_view("KanbanPage")),
            ("List View", lambda: self.controller.show_view("ListViewPage"))
        ]

        for text, command in buttons:
            btn = tk.Button(nav_frame, text=text, command=command,
                            bg=COLORS['primary_bg'], fg=COLORS['primary_accent'],
                            font=FONTS['bold'], relief='flat', bd=0,
                            activebackground=COLORS['secondary_bg'])
            btn.pack(side='right', padx=10)

    def show_user_menu(self, event):
        # Get Username
        username = getattr(self.controller, 'current_user', 'User')

        menu_options = [
            (f"Header: {username}", None),
            ("---", None),
            ("Profile", lambda: self.controller.show_view("ProfilePage")),
            ("Settings", lambda: self.controller.show_view("SettingsPage")),
            ("Logout", self.controller.logout)
        ]
        
        # Launch Custom Dropdown
        DropdownMenu(self.winfo_toplevel(), self.user_btn, menu_options)

class DropdownMenu(tk.Toplevel):
    def __init__(self, parent, target_widget, options):
        super().__init__(parent)
        self.target = target_widget
        self.options = options
        
        # Window Configuration
        self.overrideredirect(True) 
        self.config(bg=COLORS['primary_accent']) 
        self.attributes('-topmost', True)
        
        # Container for items
        self.container = tk.Frame(self, bg=COLORS['primary_bg'])
        self.container.pack(fill='both', expand=True, padx=1, pady=1)
        
        # Add Menu Items
        for text, command in options:
            if text == "---": # Separator
                tk.Frame(self.container, height=1, bg='gray').pack(fill='x', pady=5)
            elif text.startswith("Header:"): # Non-clickable Header
                tk.Label(self.container, text=text.replace("Header:", ""), 
                         font=FONTS['bold'], fg=COLORS['primary_accent'], bg=COLORS['primary_bg'], 
                         anchor='w', padx=15, pady=5).pack(fill='x')
            else:
                btn = tk.Button(self.container, text=text, command=lambda cmd=command: self.on_click(cmd),
                                font=FONTS['default'], bg=COLORS['primary_bg'], fg=COLORS['primary_txt'],
                                activebackground=COLORS['secondary_bg'], activeforeground=COLORS['primary_accent'],
                                bd=0, relief='flat', anchor='w', padx=15, pady=8, cursor='hand2')
                btn.pack(fill='x')
                
                # Hover Effect
                btn.bind("<Enter>", lambda e, b=btn: b.config(bg=COLORS['primary_accent'], fg='white'))
                btn.bind("<Leave>", lambda e, b=btn: b.config(bg=COLORS['primary_bg'], fg=COLORS['primary_txt']))

        # Click Outside to close
        self.bind("<FocusOut>", lambda e: self.destroy())
        
        # Calculate Position
        self.update_idletasks()
        self.place_menu()
        
        self.focus_set()

    def place_menu(self):
        self.update_idletasks()
        
        # Get Button Coordinates
        btn_x = self.target.winfo_rootx()
        btn_y = self.target.winfo_rooty()
        btn_h = self.target.winfo_height()
        btn_w = self.target.winfo_width()
        
        # Get Menu Dimensions
        menu_w = self.container.winfo_reqwidth() + 4
        menu_h = self.container.winfo_reqheight() + 4
        
        # Right Alignment
        x = (btn_x + btn_w) - menu_w
        y = btn_y + btn_h + 2

        if x < 0:
            x = btn_x 
            
        self.geometry(f"{menu_w}x{menu_h}+{x}+{y}")

    def on_click(self, command):
        self.destroy()
        command()

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