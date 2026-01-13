import tkinter as tk
from tkinter import messagebox
from utils.config import COLORS, FONTS
from utils.components import Header, create_input_field

class SettingsPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLORS['primary_bg'])
        self.controller = controller
        Header(self, controller, show_nav=True).pack(fill='x')

        container = tk.Frame(self, bg=COLORS['primary_bg'], padx=40, pady=10)
        container.pack(fill='both', expand=True)

        # Account Settings
        tk.Label(container, text="Account Settings", font=FONTS['header'], 
                 bg=COLORS['primary_bg'], fg=COLORS['primary_accent']).pack(anchor='w', pady=0)

        acct_frame = tk.Frame(container, bg=COLORS['primary_bg'], padx=20, pady=20, bd=1, relief='groove')
        acct_frame.pack(fill='x', pady=(0, 30))

        current_user = getattr(self.controller, 'current_user', '')
        self.new_user_var = tk.StringVar(value=current_user)
        self.new_pass_var = tk.StringVar()
        self.confirm_pass_var = tk.StringVar()

        create_input_field(acct_frame, "Username:", self.new_user_var, 0, 0, 'entry')
        create_input_field(acct_frame, "New Password:", self.new_pass_var, 1, 0, 'entry', mask=True)
        create_input_field(acct_frame, "Confirm Password:", self.confirm_pass_var, 2, 0, 'entry', mask=True)
        
        tk.Button(acct_frame, text="Update Account", command=self.save_account,
                  bg=COLORS['primary_accent'], fg='white', font=FONTS['bold']).grid(row=3, column=1, sticky='e', pady=10)

    def tkraise(self, *args, **kwargs):
        super().tkraise(*args, **kwargs)
        
        # Refresh Account Fields
        current_user = getattr(self.controller, 'current_user', '')
        self.new_user_var.set(current_user)
        self.new_pass_var.set('')
        self.confirm_pass_var.set('')

    def save_account(self):
        user = self.new_user_var.get().strip()
        pw = self.new_pass_var.get().strip()
        confirm = self.confirm_pass_var.get().strip()

        if not user:
            messagebox.showwarning("Error", "Username cannot be empty.")
            return

        if pw and pw != confirm:
            messagebox.showerror("Error", "Passwords do not match.")
            return
        
        success = self.controller.db.update_credentials(
            self.controller.current_user_id, user, pw
        )
        
        if success:
            messagebox.showinfo("Success", "Account updated! Please login again.")
            self.controller.logout()
        else:
            messagebox.showerror("Error", "Username already taken.")
