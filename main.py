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

myappid = 'student.taskflow.app.1.0' 
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except ImportError:
    pass

class TaskApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Task Management System')
        self.geometry('1100x700')

        base_folder = os.path.dirname(__file__)
        image_path = os.path.join(base_folder, 'assets', 'logo.png')
        logo_img = tk.PhotoImage(file=image_path)
        self.iconphoto(False, logo_img)

        self.configure(bg=COLORS['primary_bg'])
        
        setup_styles(self)
        self.db = Database()
        self.current_user_id = None
        self.current_user = None

        self.stop_thread = False
        
        # Container for pages
        self.container = tk.Frame(self, bg=COLORS['primary_bg'])
        self.container.pack(fill='both', expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        
        self.frames = {}
        self.init_frames()
        self.show_view("LoginPage")

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def init_frames(self):
        for F in (login.LoginPage, register.RegisterPage, 
                  listview.ListViewPage, kanban.KanbanPage, 
                  settings.SettingsPage, 
                  profile.ProfilePage):
            page_name = F.__name__
            frame = F(parent=self.container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

    def show_view(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()
        if hasattr(frame, 'refresh'):
            frame.refresh()

    def login_success(self, user_id, username):
        self.current_user_id = user_id
        self.current_user = username
        self.show_view("KanbanPage")

        self.stop_thread = False
        self.notify_thread = threading.Thread(target=self.check_notifications, daemon=True)
        self.notify_thread.start()

    def logout(self):
        if tk.messagebox.askyesno("Logout", "Are you sure you want to log out?"):
            self.stop_thread = True
            self.current_user_id = None
            self.current_user = None
            self.show_view("LoginPage")

    def on_close(self):
        if self.current_user_id:
            ans = messagebox.askyesnocancel("Exit TaskFlow", "Do you want to minimize to background?")
            
            if ans is True:
                self.iconify()
            elif ans is False:
                self.stop_thread = True
                self.destroy()
        else:
            self.stop_thread = True
            self.destroy()

    def check_notifications(self):
        time.sleep(2) 
        
        while not self.stop_thread:
            if self.current_user_id:
                tasks = self.db.get_due_today(self.current_user_id)
                
                if tasks:
                    count = len(tasks)
                    title_text = "TaskFlow Reminder"
                    msg_text = f"You have {count} tasks due today!"

                    icon_path = os.path.abspath(os.path.join("assets", "icon.ico"))

                    try:
                        notification.notify(
                            title=title_text,
                            message=msg_text,
                            app_name='TaskFlow',
                            app_icon=icon_path if os.path.exists(icon_path) else None,
                            timeout=10
                        )
                    except Exception as e:
                        print(f"Notification failed: {e}")

            # Check again in 1 hour
            for _ in range(3600): 
                if self.stop_thread: break
                time.sleep(1)

if __name__ == "__main__":
    app = TaskApp()
    app.mainloop()