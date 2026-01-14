import tkinter as tk
from tkinter import ttk, messagebox
from utils.config import COLORS, FONTS
from utils.components import Header, create_input_field

class SettingsPage(tk.Frame):
    """Settings page for updating profile and security details"""

    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLORS['primary_bg'])
        self.controller = controller

        # Header with navigation
        self.header = Header(self, controller, show_nav=True)
        self.header.pack(fill='x')

        # --- SCROLLABLE CONTAINER SETUP ---
        self.canvas = tk.Canvas(self, bg=COLORS['primary_bg'], highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=COLORS['primary_bg'], padx=40, pady=20)

        # Update scroll region dynamically
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # ================= PROFILE SECTION =================
        tk.Label(
            self.scrollable_frame,
            text="Profile",
            font=FONTS['header'],
            bg=COLORS['primary_bg'],
            fg=COLORS['primary_accent']
        ).pack(anchor='w', pady=(0, 10))

        user_frame = tk.LabelFrame(
            self.scrollable_frame,
            text=" Change Username ",
            font=FONTS['bold'],
            bg=COLORS['primary_bg'],
            fg=COLORS['primary_txt'],
            padx=20,
            pady=20,
            bd=0
        )
        user_frame.pack(fill='x', pady=(0, 30))

        # Username change variables
        self.new_username_var = tk.StringVar()
        self.user_current_pass_var = tk.StringVar()

        # Inputs
        create_input_field(user_frame, "New Username:", self.new_username_var, 0, 0, 'entry')
        create_input_field(user_frame, "Current Password:", self.user_current_pass_var, 1, 0, 'entry', mask=True)

        tk.Button(
            user_frame,
            text="Update Username",
            command=self.update_username,
            bg=COLORS['primary_accent'],
            fg='white',
            font=FONTS['bold']
        ).grid(row=2, column=1, sticky='e', pady=10)

        # ================= SECURITY SECTION =================
        tk.Label(
            self.scrollable_frame,
            text="Security",
            font=FONTS['header'],
            bg=COLORS['primary_bg'],
            fg=COLORS['primary_accent']
        ).pack(anchor='w', pady=(0, 10))

        pass_frame = tk.LabelFrame(
            self.scrollable_frame,
            text=" Change Password ",
            font=FONTS['bold'],
            bg=COLORS['primary_bg'],
            fg=COLORS['primary_txt'],
            padx=20,
            pady=20,
            bd=0
        )
        pass_frame.pack(fill='x', pady=(0, 30))

        # Password change variables
        self.pass_current_var = tk.StringVar()
        self.pass_new_var = tk.StringVar()
        self.pass_confirm_var = tk.StringVar()

        # Inputs
        create_input_field(pass_frame, "Current Password:", self.pass_current_var, 0, 0, 'entry', mask=True)
        create_input_field(pass_frame, "New Password:", self.pass_new_var, 1, 0, 'entry', mask=True)
        create_input_field(pass_frame, "Confirm Password:", self.pass_confirm_var, 2, 0, 'entry', mask=True)

        tk.Button(
            pass_frame,
            text="Update Password",
            command=self.update_password,
            bg=COLORS['primary_accent'],
            fg='white',
            font=FONTS['bold']
        ).grid(row=3, column=1, sticky='e', pady=10)

    def tkraise(self, *args, **kwargs):
        """Refresh fields when page becomes active"""
        super().tkraise(*args, **kwargs)

        # Pre-fill username
        current_name = getattr(self.controller, 'current_user', '')
        self.new_username_var.set(current_name)

        # Clear password fields
        self.user_current_pass_var.set('')
        self.pass_current_var.set('')
        self.pass_new_var.set('')
        self.pass_confirm_var.set('')

    # ---------------- USERNAME UPDATE LOGIC ----------------
    def update_username(self):
        new_user = self.new_username_var.get().strip()
        current_pass = self.user_current_pass_var.get().strip()

        # Basic validation
        if not new_user or not current_pass:
            messagebox.showwarning("Error", "Please enter the new username and your current password.")
            return

        if len(new_user) < 4 or len(new_user) > 20:
            messagebox.showwarning("Invalid Username", "Username must be between 4 and 20 characters.")
            return

        # Verify password
        user_id = self.controller.db.verify_user(self.controller.current_user, current_pass)
        if not user_id:
            messagebox.showerror("Error", "Incorrect Password.")
            return

        # Update username only
        success = self.controller.db.update_credentials(user_id, new_user, None)

        if success:
            self.controller.update_session_user(new_user)
            messagebox.showinfo("Success", "Username updated successfully!")
            self.user_current_pass_var.set('')
        else:
            messagebox.showerror("Error", "Username already taken.")

    # ---------------- PASSWORD UPDATE LOGIC ----------------
    def update_password(self):
        current_pass = self.pass_current_var.get().strip()
        new_pass = self.pass_new_var.get().strip()
        confirm_pass = self.pass_confirm_var.get().strip()

        # Basic validation
        if not current_pass or not new_pass or not confirm_pass:
            messagebox.showwarning("Error", "Please fill in all fields.")
            return

        if len(new_pass) < 8:
            messagebox.showwarning("Invalid Password", "Password must be at least 8 characters long.")
            return

        if new_pass != confirm_pass:
            messagebox.showerror("Error", "New passwords do not match.")
            return

        # Verify current password
        user_id = self.controller.db.verify_user(self.controller.current_user, current_pass)
        if not user_id:
            messagebox.showerror("Error", "Current password is incorrect.")
            return

        # Update password only
        success = self.controller.db.update_credentials(
            user_id,
            self.controller.current_user,
            new_pass
        )

        if success:
            messagebox.showinfo("Success", "Password updated! Please login again.")
            self.controller.logout(prompt=False)
        else:
            messagebox.showerror("Error", "Failed to update password.")
