import tkinter as tk
from tkinter import messagebox
from utils.config import COLORS, FONTS
from utils.components import Header, create_input_field
from re import fullmatch

class RegisterPage(tk.Frame):
    """User registration page"""

    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLORS['primary_bg'])
        self.controller = controller

        # Header without navigation
        Header(self, controller, show_nav=False).pack(fill='x')

        # Centered container
        container = tk.Frame(
            self,
            bg=COLORS['primary_bg'],
            bd=1,
            relief='groove',
            padx=30,
            pady=30
        )
        container.place(relx=0.5, rely=0.5, anchor='center')

        tk.Label(
            container,
            text="Create Account",
            font=FONTS['header'],
            bg=COLORS['primary_bg'],
            fg=COLORS['primary_accent']
        ).pack(pady=(0, 20))

        # Form variables
        self.user_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.pass_var = tk.StringVar()
        self.confirm_var = tk.StringVar()

        # Input fields
        input_frame = tk.Frame(container, bg=COLORS['primary_bg'])
        input_frame.pack(fill='x', pady=(0, 20))

        create_input_field(input_frame, "Username:", self.user_var, 0, 0, 'entry')
        create_input_field(input_frame, "Email:", self.email_var, 1, 0, 'entry')
        create_input_field(input_frame, "Password:", self.pass_var, 2, 0, 'entry', mask=True)
        create_input_field(input_frame, "Confirm Password:", self.confirm_var, 3, 0, 'entry', mask=True)

        # Register button
        tk.Button(
            container,
            text="Sign Up",
            command=self.attempt_register,
            font=FONTS['bold'],
            bg=COLORS['primary_accent'],
            fg='white'
        ).pack(fill='x', pady=10)

        # Navigation back to login
        tk.Button(
            container,
            text="Back to Login",
            command=lambda: controller.show_view("LoginPage"),
            font=FONTS['small'],
            bg=COLORS['primary_bg'],
            fg='gray',
            bd=0
        ).pack()

    def attempt_register(self):
        """Validate input and create a new user account"""
        username = self.user_var.get().strip()
        email = self.email_var.get().strip()
        password = self.pass_var.get()
        confirm = self.confirm_var.get()

        # Basic validation
        if not username or not password:
            messagebox.showwarning("Input Error", "Please fill in all fields.")
            return

        if len(username) < 4 or len(username) > 20:
            messagebox.showwarning("Invalid Username", "Username must be between 4 and 20 characters.")
            return
        
        regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not fullmatch(regex, email):
            messagebox.showwarning("Invalid Email", "Email must be a valid email.")
            return

        if len(password) < 8:
            messagebox.showwarning("Invalid Password", "Password must be at least 8 characters long.")
            return

        if password != confirm:
            messagebox.showerror("Password Error", "Passwords do not match.")
            return

        # Create user
        success = self.controller.db.create_user(username, email, password)

        if success:
            messagebox.showinfo("Signup Success", "Account created successfully!\nPlease log in.")
            self.user_var.set("")
            self.email_var.set("")
            self.pass_var.set("")
            self.confirm_var.set("")
            self.controller.show_view("LoginPage")
        else:
            messagebox.showerror("Signup Error", "Username or email already exists. Please enter another.")
