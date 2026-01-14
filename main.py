import tkinter as tk
from tkinter import messagebox
from utils.config import setup_styles, COLORS
from database import Database
from pages import login, register, listview, kanban, settings, profile
import os
import threading
import time
from plyer import notification
import ctypes
import sys

# Windows App ID for notifications
myappid = 'taskflow.app'
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except ImportError:
    pass

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class TaskApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.withdraw()

        # Main window settings
        self.title('Task Management System')
        self.geometry('1100x700')
        self.minsize(1100, 700)

        # Set application icon
        base_folder = os.path.dirname(__file__)
        image_path = os.path.join(base_folder, 'assets', 'logo.png')
        logo_img = tk.PhotoImage(file=image_path)
        self.iconphoto(False, logo_img)

        # Apply background color and styles
        self.configure(bg=COLORS['primary_bg'])
        setup_styles(self)

        # Initialize database and user session
        self.db = Database()
        self.current_user_id = None
        self.current_user = None

        # Notification thread control
        self.stop_thread = False

        # Container for all pages
        self.container = tk.Frame(self, bg=COLORS['primary_bg'])
        self.container.pack(fill='both', expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # Initialize pages
        self.frames = {}
        self.init_frames()
        self.show_view("LoginPage")
        self.deiconify()

        # Handle window close event
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def init_frames(self):
        # Create and store all page frames
        for F in (
            register.RegisterPage,
            listview.ListViewPage,
            kanban.KanbanPage,
            settings.SettingsPage,
            profile.ProfilePage,
            login.LoginPage
        ):
            page_name = F.__name__
            frame = F(parent=self.container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

    def show_view(self, page_name):
        # Raise the selected page
        frame = self.frames[page_name]
        frame.tkraise()
        if hasattr(frame, 'refresh'):
            frame.refresh()

    def login_success(self, user_id, username):
        # Set user session after login
        self.current_user_id = user_id
        self.current_user = username
        self.show_view("KanbanPage")

        # Start notification checker
        self.stop_thread = False
        self.notify_thread = threading.Thread(
            target=self.check_notifications,
            daemon=True
        )
        self.notify_thread.start()

    def logout(self, prompt=True):
        # Logout without confirmation
        if not prompt:
            self.stop_thread = True
            self.current_user_id = None
            self.current_user = None
            self.show_view("LoginPage")
            return

        # Logout with confirmation
        if tk.messagebox.askyesno("Logout", "Are you sure you want to log out?"):
            self.stop_thread = True
            self.current_user_id = None
            self.current_user = None
            self.show_view("LoginPage")

    def update_session_user(self, new_username):
        # Update username in session
        self.current_user = new_username

    def on_close(self):
        # Handle app exit behavior
        if self.current_user_id:
            ans = messagebox.askyesnocancel(
                "Exit TaskFlow",
                "Are you sure you want to exit TaskFlow?"
            )

            if ans is False:
                self.iconify()
            elif ans is True:
                self.stop_thread = True
                self.destroy()
        else:
            self.stop_thread = True
            self.destroy()

    def check_notifications(self):
        # Initial delay before checking
        time.sleep(2)

        while not self.stop_thread:
            if self.current_user_id:
                # Get tasks due today
                tasks = self.db.get_due_today(self.current_user_id)

                if tasks:
                    count = len(tasks)
                    title_text = "TaskFlow Reminder"
                    msg_text = f"You have {count} task/s due or overdue today!"

                    icon_path = resource_path(os.path.join("assets", "icon.ico"))

                    try:
                        # Show desktop notification
                        notification.notify(
                            title=title_text,
                            message=msg_text,
                            app_name='TaskFlow',
                            app_icon=icon_path if os.path.exists(icon_path) else None,
                            timeout=10
                        )
                    except Exception as e:
                        print(f"Notification failed: {e}")

            # Check again after 6 hours
            for _ in range(21600):
                if self.stop_thread:
                    break
                time.sleep(1)


if __name__ == "__main__":
    app = TaskApp()
    app.mainloop()
