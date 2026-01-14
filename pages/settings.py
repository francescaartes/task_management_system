import tkinter as tk
from tkinter import ttk, messagebox
from utils.config import COLORS, FONTS
from utils.components import Header, create_input_field

class SettingsPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLORS['primary_bg'])
        self.controller = controller
        # Store header to update user menu later
        self.header = Header(self, controller, show_nav=True)
        self.header.pack(fill='x')

        # Scrollable Container Setup
        self.canvas = tk.Canvas(self, bg=COLORS['primary_bg'], highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=COLORS['primary_bg'], padx=40, pady=20)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # --- SECTION 1: CHANGE USERNAME ---
        tk.Label(self.scrollable_frame, text="Profile", font=FONTS['header'], 
                 bg=COLORS['primary_bg'], fg=COLORS['primary_accent']).pack(anchor='w', pady=(0, 10))

        user_frame = tk.LabelFrame(self.scrollable_frame, text=" Change Username ", font=FONTS['bold'],
                                   bg=COLORS['primary_bg'], fg=COLORS['primary_txt'], padx=20, pady=20, bd=0)
        user_frame.pack(fill='x', pady=(0, 30))

        self.new_username_var = tk.StringVar()
        self.user_current_pass_var = tk.StringVar() # Password field specifically for changing username

        # Inputs
        create_input_field(user_frame, "New Username:", self.new_username_var, 0, 0, 'entry')
        create_input_field(user_frame, "Current Password:", self.user_current_pass_var, 1, 0, 'entry', mask=True)
        
        tk.Button(user_frame, text="Update Username", command=self.update_username,
                  bg=COLORS['primary_accent'], fg='white', font=FONTS['bold']).grid(row=2, column=1, sticky='e', pady=10)

        # --- SECTION 2: CHANGE PASSWORD ---
        tk.Label(self.scrollable_frame, text="Security", font=FONTS['header'], 
                 bg=COLORS['primary_bg'], fg=COLORS['primary_accent']).pack(anchor='w', pady=(0, 10))

        pass_frame = tk.LabelFrame(self.scrollable_frame, text=" Change Password ", font=FONTS['bold'],
                                   bg=COLORS['primary_bg'], fg=COLORS['primary_txt'], padx=20, pady=20, bd=0)
        pass_frame.pack(fill='x', pady=(0, 30))

        self.pass_current_var = tk.StringVar()
        self.pass_new_var = tk.StringVar()
        self.pass_confirm_var = tk.StringVar()

        # Inputs
        create_input_field(pass_frame, "Current Password:", self.pass_current_var, 0, 0, 'entry', mask=True)
        create_input_field(pass_frame, "New Password:", self.pass_new_var, 1, 0, 'entry', mask=True)
        create_input_field(pass_frame, "Confirm Password:", self.pass_confirm_var, 2, 0, 'entry', mask=True)

        tk.Button(pass_frame, text="Update Password", command=self.update_password,
                  bg=COLORS['primary_accent'], fg='white', font=FONTS['bold']).grid(row=3, column=1, sticky='e', pady=10)

    def tkraise(self, *args, **kwargs):
        super().tkraise(*args, **kwargs)
        
        # Pre-fill current username
        current_name = getattr(self.controller, 'current_user', '')
        self.new_username_var.set(current_name)
        
        # Clear all password fields
        self.user_current_pass_var.set('')
        self.pass_current_var.set('')
        self.pass_new_var.set('')
        self.pass_confirm_var.set('')

    # --- LOGIC: UPDATE USERNAME ---
    def update_username(self):
        new_user = self.new_username_var.get().strip()
        current_pass = self.user_current_pass_var.get().strip()
        
        if not new_user or not current_pass:
            messagebox.showwarning("Error", "Please enter the new username and your current password.")
            return
        
        if len(new_user) < 4 or len(new_user) > 20:
            messagebox.showwarning("Invalid Username", "Username must be between 4 and 20 characters.")
            return

        # 1. Verify Current Password First
        user_id = self.controller.db.verify_user(self.controller.current_user, current_pass)
        if not user_id:
            messagebox.showerror("Error", "Incorrect Password.")
            return

        # 2. Update Only Username (pass None for password)
        success = self.controller.db.update_credentials(user_id, new_user, None)
        
        if success:
            self.controller.update_session_user(new_user)
            messagebox.showinfo("Success", "Username updated successfully!")
            self.user_current_pass_var.set('') # Clear pass field
        else:
            messagebox.showerror("Error", "Username already taken.")

    # --- LOGIC: UPDATE PASSWORD ---
    def update_password(self):
        current_pass = self.pass_current_var.get().strip()
        new_pass = self.pass_new_var.get().strip()
        confirm_pass = self.pass_confirm_var.get().strip()

        if not current_pass or not new_pass or not confirm_pass:
            messagebox.showwarning("Error", "Please fill in all fields.")
            return
        
        if len(new_pass) < 8:
            messagebox.showwarning("Invalid Password", "Password must be at least 8 characters long.")
            return

        # 1. Check New Passwords Match
        if new_pass != confirm_pass:
            messagebox.showerror("Error", "New passwords do not match.")
            return

        # 2. Verify Current Password
        # We use the stored username to verify ownership
        user_id = self.controller.db.verify_user(self.controller.current_user, current_pass)
        if not user_id:
            messagebox.showerror("Error", "Current password is incorrect.")
            return

        # 3. Update Only Password (keep current username)
        success = self.controller.db.update_credentials(user_id, self.controller.current_user, new_pass)
        
        if success:
            messagebox.showinfo("Success", "Password updated! Please login again.")
            self.controller.logout(prompt=False)
        else:
            messagebox.showerror("Error", "Failed to update password.")