import tkinter as tk
from tkinter import messagebox
from utils.config import COLORS, FONTS
from utils.components import Header, create_input_field

class LoginPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLORS['primary_bg'])
        self.controller = controller
        Header(self, controller, show_nav=False).pack(fill='x')
        
        # Login Container
        container = tk.Frame(
            self, 
            bg=COLORS['primary_bg'], 
            borderwidth=1, 
            relief='groove',
            padx=20,
            pady=20
        )
        container.place(relx=0.5, rely=0.5, anchor='center')
        
        # Welcome Back
        tk.Label(
            container,
            text='Welcome back',
            font=FONTS['header'],
            bg=COLORS['primary_bg'],
            fg=COLORS['primary_accent'],
            padx=20,
            pady=20
        ).pack(anchor='w')
        
        # Username and Password
        self.user_var = tk.StringVar()
        self.pass_var = tk.StringVar()
        
        # Inputs
        input_frame = tk.Frame(
            container,
            bg=COLORS['primary_bg'],
        )
        input_frame.pack(fill='x', pady=(0, 20), padx=20)
        user_entry = create_input_field(input_frame, 'Username:', self.user_var, 0, 0, 'entry')
        pass_entry = create_input_field(input_frame, 'Password:', self.pass_var, 1, 0, 'entry', mask=True)

        if user_entry: user_entry.bind('<Return>', self.check_login)
        if pass_entry: pass_entry.bind('<Return>', self.check_login)
        
        # Login Button
        btn_frame = tk.Frame(
            container,
            bg=COLORS['primary_bg']
        )
        btn_frame.pack(fill='x', pady=(0, 20), padx=20)
        tk.Button(
            btn_frame,
            text='Login',
            command=self.check_login,
            font=FONTS['bold'],
            bg=COLORS['primary_accent'],
            fg=COLORS['secondary_txt']
        ).pack(fill='x', anchor='center')
        
        # Sign Up Button
        signup_frame = tk.Frame(btn_frame, bg=COLORS['primary_bg'])
        signup_frame.pack(fill='x', anchor='center', pady=(10, 0))
        
        tk.Label(
            signup_frame,
            text="Don't have an account? ",
            font=FONTS['small'],
            bg=COLORS['primary_bg'],
            fg=COLORS['primary_txt']
        ).pack(side='left', anchor='center')
        
        signup_btn = tk.Button(
            signup_frame,
            text="Sign Up",
            command=lambda: controller.show_view("RegisterPage"),
            font=('Verdana', 9, 'bold'), 
            bg=COLORS['primary_bg'],      
            fg=COLORS['primary_accent'],
            activebackground=COLORS['primary_bg'],
            activeforeground=COLORS['primary_txt'],
            bd=0, 
            relief='flat',
            cursor='hand2'
        )
        signup_btn.pack(side='left', anchor='center')

    def check_login(self, event=None):
        user = self.user_var.get()
        pw = self.pass_var.get()
        user_id = self.controller.db.verify_user(user, pw)
        
        if  user_id:
            self.controller.login_success(user_id, user)
        else:
            messagebox.showerror("Login Error", "Incorrect username or password. Please try again.")
