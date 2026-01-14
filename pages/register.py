import tkinter as tk
from tkinter import messagebox
from utils.config import COLORS, FONTS
from utils.components import Header, create_input_field


class RegisterPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLORS['primary_bg'])
        self.controller = controller
        Header(self, controller, show_nav=False).pack(fill='x')

        container = tk.Frame(self, bg=COLORS['primary_bg'], bd=1, relief='groove', padx=30, pady=30)
        container.place(relx=0.5, rely=0.5, anchor='center')

        tk.Label(container, text="Create Account", font=FONTS['header'], 
                 bg=COLORS['primary_bg'], fg=COLORS['primary_accent']).pack(pady=(0, 20))

        # Variables
        self.user_var = tk.StringVar()
        self.pass_var = tk.StringVar()
        self.confirm_var = tk.StringVar()

        # Input Fields
        input_frame = tk.Frame(container, bg=COLORS['primary_bg'])
        input_frame.pack(fill='x', pady=(0, 20))
        
        create_input_field(input_frame, "Username:", self.user_var, 0, 0, 'entry')
        create_input_field(input_frame, "Password:", self.pass_var, 1, 0, 'entry', mask=True)
        create_input_field(input_frame, "Confirm Password:", self.confirm_var, 2, 0, 'entry', mask=True)

        # Register Button
        tk.Button(container, text="Sign Up", command=self.attempt_register,
                  font=FONTS['bold'], bg=COLORS['primary_accent'], fg='white').pack(fill='x', pady=10)

        # Back to Login
        tk.Button(container, text="Back to Login", command=lambda: controller.show_view("LoginPage"),
                  font=FONTS['small'], bg=COLORS['primary_bg'], fg='gray', bd=0).pack()

    def attempt_register(self):
        username = self.user_var.get().strip()
        password = self.pass_var.get()
        confirm = self.confirm_var.get()

        if not username or not password:
            messagebox.showwarning("Input Error", "Please fill in all fields.")
            return
        
        if len(username) < 4 or len(username) > 20:
            messagebox.showwarning("Invalid Username", "Username must be between 4 and 20 characters.")
            return

        if len(password) < 8:
            messagebox.showwarning("Invalid Password", "Password must be at least 8 characters long.")
            return

        if password != confirm:
            messagebox.showerror("Password Error", "Passwords do not match.")
            return

        success = self.controller.db.create_user(username, password)
        
        if success:
            messagebox.showinfo("Signup Success", "Account created successfully!\nPlease log in.")
            self.controller.show_view("LoginPage")
        else:
            messagebox.showerror("Signup Error", "Username already exists. Please choose another.")
