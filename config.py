import tkinter as tk
import os
from dotenv import load_dotenv

# DB_FILE = 'task_management.db'

# ADMIN_USER = ''
# ADMIN_PASS = ''

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_PORT = os.getenv("DB_PORT")

COLORS = {
    'primary_bg': "#F8F8FF",
    'secondary_bg': "#E0E0E8",
    'primary_txt': "#1A1A1A",
    'secondary_txt': "#EEEEEE",
    'primary_accent': '#2B3A7E',
    'white': '#FFFFFF',
    'danger': '#FF4444'
}

FONTS = {
    'default': ('Verdana', 12),
    'bold': ('Verdana', 12, 'bold'),
    'header': ('Verdana', 20, 'bold'),
    'small': ('Verdana', 9)
}

def setup_styles(root):
    """Initialize TTK styles"""
    style = tk.ttk.Style()
    style.theme_use('default')

    style.configure(
        "Treeview",
        background=COLORS['primary_bg'],
        foreground=COLORS['primary_txt'],
        fieldbackground=COLORS['primary_bg'],
        font=FONTS['default'],
        rowheight=25
    )
    style.map("Treeview", background=[("selected", COLORS['primary_accent'])])
    
    style.configure(
        "Treeview.Heading",
        background=COLORS['secondary_bg'],
        foreground=COLORS['primary_accent'],
        font=FONTS['bold'],
        padding=5
    )

    root.option_add('*TCombobox*Listbox.background', COLORS['secondary_bg'])
    root.option_add('*TCombobox*Listbox.foreground', COLORS['primary_txt'])
    root.option_add('*TCombobox*Listbox.selectBackground', COLORS['primary_accent'])
    root.option_add('*TCombobox*Listbox.selectForeground', COLORS['secondary_txt'])

    style.map('TCombobox',
        fieldbackground=[('readonly', COLORS['secondary_bg'])],
        selectbackground=[('readonly', COLORS['secondary_bg'])],
        selectforeground=[('readonly', COLORS['primary_txt'])]
    )
    style.configure('TCombobox',
        background=COLORS['secondary_bg'],
        foreground=COLORS['primary_txt'],
        arrowcolor=COLORS['primary_txt'],
        fieldbackground=COLORS['secondary_bg']
    )