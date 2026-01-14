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
        
        # Load application logo
        logo_img = self.resource_path("assets/icon.png")
        try:
            logo_img = tk.PhotoImage(file=logo_img)
        except:
            logo_img = None
        self.logo_img = logo_img 
        
        # Logo and app title
        tk.Label(self, image=logo_img, bg=COLORS['primary_bg']).pack(side='left', padx=(20, 10), pady=10) 
        tk.Label(self, text='TaskFlow', font=FONTS['header'], 
                 bg=COLORS['primary_bg'], fg=COLORS['primary_accent']).pack(side='left')

        # Load user icon
        user_path = self.resource_path("assets/user.png")
        try:
            self.user_img = tk.PhotoImage(file=user_path)
        except:
            self.user_img = None

        # Navigation buttons
        if show_nav:
            self.create_nav_buttons()

    def resource_path(self, relative_path):
        # Resolve resource path for bundled or local execution
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

    def create_nav_buttons(self):
        # Right-side navigation container
        nav_frame = tk.Frame(self, bg=COLORS['primary_bg'])
        nav_frame.pack(side='right', padx=20)

        # User button (icon or fallback text)
        if self.user_img:
            self.user_btn = tk.Button(nav_frame, image=self.user_img, 
                                      bg=COLORS['primary_bg'], bd=0, 
                                      activebackground=COLORS['primary_bg'],
                                      cursor='hand2')
        else:
            # Text fallback if image is unavailable
            self.user_btn = tk.Button(nav_frame, text="👤 ", font=("Arial", 16),
                                      bg=COLORS['primary_bg'], fg=COLORS['primary_accent'], bd=0,
                                      activebackground=COLORS['primary_bg'],
                                      cursor='hand2')
            
        self.user_btn.pack(side='right', padx=(10, 0))
        
        # Open user menu on click
        self.user_btn.bind("<Button-1>", self.show_user_menu)

        # Navigation page buttons
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
        # Get current username
        username = getattr(self.controller, 'current_user', 'User')

        # User menu options
        menu_options = [
            (f"Header: {username}", None),
            ("---", None),
            ("Profile", lambda: self.controller.show_view("ProfilePage")),
            ("Settings", lambda: self.controller.show_view("SettingsPage")),
            ("Logout", self.controller.logout)
        ]
        
        # Display dropdown menu
        DropdownMenu(self.winfo_toplevel(), self.user_btn, menu_options)

    def update_username_label(self, new_name):
        # Update username display if present
        if hasattr(self, 'user_label'):
            self.user_label.config(text=new_name)


class DropdownMenu(tk.Toplevel):
    def __init__(self, parent, target_widget, options):
        super().__init__(parent)
        self.target = target_widget
        self.options = options
        
        # Popup window configuration
        self.overrideredirect(True) 
        self.config(bg=COLORS['primary_accent']) 
        self.attributes('-topmost', True)
        
        # Main container
        self.container = tk.Frame(self, bg=COLORS['primary_bg'])
        self.container.pack(fill='both', expand=True, padx=1, pady=1)
        
        # Build menu items
        for text, command in options:
            if text == "---":
                # Divider
                tk.Frame(self.container, height=1, bg='gray').pack(fill='x', pady=5)
            elif text.startswith("Header:"):
                # Menu header
                tk.Label(self.container, text=text.replace("Header:", ""), 
                         font=FONTS['bold'], fg=COLORS['primary_accent'], bg=COLORS['primary_bg'], 
                         anchor='w', padx=15, pady=5).pack(fill='x')
            else:
                # Menu button
                btn = tk.Button(self.container, text=text, command=lambda cmd=command: self.on_click(cmd),
                                font=FONTS['default'], bg=COLORS['primary_bg'], fg=COLORS['primary_txt'],
                                activebackground=COLORS['secondary_bg'], activeforeground=COLORS['primary_accent'],
                                bd=0, relief='flat', anchor='w', padx=15, pady=8, cursor='hand2')
                btn.pack(fill='x')
                
                # Hover styling
                btn.bind("<Enter>", lambda e, b=btn: b.config(bg=COLORS['primary_accent'], fg='white'))
                btn.bind("<Leave>", lambda e, b=btn: b.config(bg=COLORS['primary_bg'], fg=COLORS['primary_txt']))

        # Close menu when focus is lost
        self.bind("<FocusOut>", lambda e: self.destroy())
        
        # Position menu near target widget
        self.update_idletasks()
        self.place_menu()
        
        self.focus_set()

    def place_menu(self):
        # Compute menu position relative to target
        self.update_idletasks()
        
        btn_x = self.target.winfo_rootx()
        btn_y = self.target.winfo_rooty()
        btn_h = self.target.winfo_height()
        btn_w = self.target.winfo_width()
        
        menu_w = self.container.winfo_reqwidth() + 4
        menu_h = self.container.winfo_reqheight() + 4
        
        x = (btn_x + btn_w) - menu_w
        y = btn_y + btn_h + 2

        if x < 0:
            x = btn_x 
            
        self.geometry(f"{menu_w}x{menu_h}+{x}+{y}")

    def on_click(self, command):
        # Execute menu action
        self.destroy()
        command()


def create_input_field(parent, label_text, var, row, col, input_type, mask=False):
    # Input label
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
            # Single-line text input
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
            # Multi-line text input
            text_container = tk.Frame(parent, bg=COLORS['primary_bg'])
            text_container.grid(row=row + 1, column=0, columnspan=2, sticky='ew', padx=10, pady=(0, 10))
            
            scrollbar = ttk.Scrollbar(text_container)
            scrollbar.pack(side='right', fill='y')
            
            textarea = tk.Text(
                text_container,
                wrap=tk.WORD,
                height=5,
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
            # Status selection dropdown
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
            # Date and time selector container
            input_frame = tk.Frame(parent, bg=COLORS['primary_bg'])
            input_frame.grid(row=row, column=col+1, sticky='ew', padx=(0, 10), pady=5)
            
            # Calendar input
            cal = DateEntry(
                input_frame, 
                width=12, 
                background=COLORS['primary_accent'],
                foreground='white', 
                borderwidth=2, 
                date_pattern='yyyy-mm-dd',
                font=FONTS['default']
            )
            cal.pack(side='top', fill='x', expand=True)

            # Time input container
            time_frame = tk.Frame(input_frame, bg=COLORS['primary_bg'])
            time_frame.pack(side='top', fill='x', pady=(5, 0))

            # Sync UI values to variable
            def update_var(event=None):
                d = cal.get_date()
                
                raw_h = hour_var.get().strip()
                raw_m = min_var.get().strip()
                
                h = int(raw_h) if raw_h.isdigit() else 0
                m = int(raw_m) if raw_m.isdigit() else 0
                
                h = max(0, min(23, h))
                m = max(0, min(59, m))
                
                if event and event.type == tk.EventType.FocusOut:
                     hour_var.set(f"{h:02d}")
                     min_var.set(f"{m:02d}")

                final_str = f"{d} {h:02d}:{m:02d}"
                
                if var.get() != final_str:
                    var.set(final_str)

            # Hour input
            hour_var = tk.StringVar(value="12")
            h_spin = tk.Spinbox(
                time_frame, from_=0, to=23, width=3, format="%02.0f", 
                textvariable=hour_var, font=FONTS['default'], wrap=True,
                bg=COLORS['secondary_bg'], fg=COLORS['primary_txt'],
                buttonbackground=COLORS['secondary_bg'],
                justify='center',
                command=update_var
            )
            h_spin.pack(side='left', fill='x', expand=True) 

            # Time separator
            tk.Label(time_frame, text=":", bg=COLORS['primary_bg'], 
                     fg=COLORS['primary_accent'], font=FONTS['bold']).pack(side='left', padx=2)

            # Minute input
            min_var = tk.StringVar(value="00")
            m_spin = tk.Spinbox(
                time_frame, from_=0, to=59, width=3, format="%02.0f", 
                textvariable=min_var, font=FONTS['default'], wrap=True,
                bg=COLORS['secondary_bg'], fg=COLORS['primary_txt'],
                buttonbackground=COLORS['secondary_bg'],
                justify='center',
                command=update_var
            )
            m_spin.pack(side='left', fill='x', expand=True)

            # Update on user interaction
            cal.bind("<<DateEntrySelected>>", update_var)
            h_spin.bind("<FocusOut>", update_var)
            h_spin.bind("<Return>", update_var)
            m_spin.bind("<FocusOut>", update_var)
            m_spin.bind("<Return>", update_var)

            # Sync variable back to UI
            def update_ui(*args):
                val = var.get()
                if not val: return
                try:
                    dt = datetime.strptime(val, '%Y-%m-%d %H:%M')
                    cal.set_date(dt.date())
                    if parent.focus_get() not in (h_spin, m_spin):
                        hour_var.set(f"{dt.hour:02d}")
                        min_var.set(f"{dt.minute:02d}")
                except ValueError:
                    try:
                        dt = datetime.strptime(val, '%Y-%m-%d')
                        cal.set_date(dt.date())
                    except ValueError:
                        pass

            var.trace_add("write", update_ui)

            # Default to current date and time
            if not var.get():
                now = datetime.now()
                var.set(now.strftime('%Y-%m-%d %H:%M'))

            return cal
        

class FilterBar(tk.Frame):
    def __init__(self, parent, controller, on_filter_command):
        super().__init__(parent, bg=COLORS['primary_bg'], padx=10, pady=10, bd=1, relief='groove')
        self.controller = controller
        self.on_filter_command = on_filter_command 

        # Filter variables
        self.search_var = tk.StringVar()
        self.cat_var = tk.StringVar(value="All Categories")
        self.status_var = tk.StringVar(value="All Status")
        self.time_var = tk.StringVar(value="Any Time")
        self.tag_var = tk.StringVar()

        # Grid layout configuration
        self.grid_columnconfigure(0, weight=0) 
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_columnconfigure(3, weight=1)

        # Search input
        tk.Label(self, text="🔎", font=FONTS['bold'], bg=COLORS['primary_bg'], fg=COLORS['primary_accent']).grid(row=0, column=0, pady=(0, 5), sticky='e')
        
        self.search_entry = tk.Entry(
            self, 
            textvariable=self.search_var, 
            font=FONTS['default'],
            bg=COLORS['secondary_bg']
        )
        self.search_entry.grid(row=0, column=1, padx=(0, 15), pady=5, sticky='ew')
        self.search_entry.bind('<Return>', lambda e: self.apply_filters())

        # Category filter
        self.cat_cb = ttk.Combobox(self, textvariable=self.cat_var, state='readonly', font=FONTS['default'])
        self.cat_cb.grid(row=0, column=2, padx=(0, 10), pady=5, sticky='ew')

        # Status filter
        self.status_cb = ttk.Combobox(self, textvariable=self.status_var, values=["All Status", "To Do", "In Progress", "Done"], state='readonly', font=FONTS['default'])
        self.status_cb.grid(row=0, column=3, pady=5, sticky='ew')

        # Tag input
        tk.Label(self, text="#", font=FONTS['bold'], bg=COLORS['primary_bg'], fg=COLORS['primary_accent']).grid(row=1, column=0, padx=(0, 5), sticky='e')
        
        self.tag_entry = tk.Entry(
            self, 
            textvariable=self.tag_var, 
            font=FONTS['default'],
            bg=COLORS['secondary_bg']
        )
        self.tag_entry.grid(row=1, column=1, padx=(0, 15), pady=5, sticky='ew')
        self.tag_entry.bind('<Return>', lambda e: self.apply_filters())

        # Timeframe filter
        self.time_cb = ttk.Combobox(self, textvariable=self.time_var, values=["Any Time", "Overdue", "Due Today", "Next 7 Days"], state='readonly', font=FONTS['default'])
        self.time_cb.grid(row=1, column=2, padx=(0, 10), pady=5, sticky='ew')

        # Action buttons
        btn_frame = tk.Frame(self, bg=COLORS['primary_bg'])
        btn_frame.grid(row=1, column=3, sticky='ew', pady=5)
        
        tk.Button(btn_frame, text="Apply", command=self.apply_filters,
                  bg=COLORS['primary_accent'], fg=COLORS['primary_bg'], font=FONTS['bold'], bd=0, padx=10).pack(side='left', padx=(0, 5), fill='x', expand=True)
        
        tk.Button(btn_frame, text="Clear", command=self.clear_filters,
                  bg=COLORS['secondary_bg'], fg=COLORS['primary_accent'], font=FONTS['bold'], bd=0, padx=5).pack(side='left', fill='x', expand=True)

        self.refresh_options()

    def refresh_options(self):
        # Refresh category options from database
        user_id = self.controller.current_user_id
        if user_id:
            cats = self.controller.db.get_all_categories(user_id)
            self.cat_cb['values'] = ["All Categories"] + cats
            
    def apply_filters(self):
        # Collect and apply filters
        filters = {
            'search': self.search_var.get().strip(),
            'category': self.cat_var.get(),
            'status': self.status_var.get(),
            'timeframe': self.time_var.get(),
            'tag': self.tag_var.get().strip()
        }
        self.on_filter_command(filters)

    def clear_filters(self):
        # Reset filters to default values
        self.search_var.set("")
        self.cat_var.set("All Categories")
        self.status_var.set("All Status")
        self.time_var.set("Any Time")
        self.tag_var.set("")
        self.apply_filters()
