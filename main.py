import tkinter as tk
from utils.config import setup_styles, COLORS
from database import Database
from pages import login, register, listview, kanban, settings, profile
import os

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
        
        # Container for pages
        self.container = tk.Frame(self, bg=COLORS['primary_bg'])
        self.container.pack(fill='both', expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        
        self.frames = {}
        self.init_frames()
        self.show_view("LoginPage")

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

    def logout(self):
        if tk.messagebox.askyesno("Logout", "Are you sure you want to log out?"):
            self.show_view("LoginPage")

if __name__ == "__main__":
    app = TaskApp()
    app.mainloop()