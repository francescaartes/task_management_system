import tkinter as tk
from tkinter import messagebox
from utils.config import COLORS, FONTS
from utils.components import Header, create_input_field
from utils.email_sender import send_reset_code 

class LoginPage(tk.Frame):
    """User login screen."""

    def __init__(self, parent, controller):
        """Initialize login UI."""
        super().__init__(parent, bg=COLORS['primary_bg'])
        self.controller = controller
        Header(self, controller, show_nav=False).pack(fill='x')
        
        container = tk.Frame(
            self,
            bg=COLORS['primary_bg'],
            borderwidth=1,
            relief='groove',
            padx=20,
            pady=20
        )
        container.place(relx=0.5, rely=0.5, anchor='center')
        
        tk.Label(
            container,
            text='Welcome back',
            font=FONTS['header'],
            bg=COLORS['primary_bg'],
            fg=COLORS['primary_accent'],
            padx=20,
            pady=20
        ).pack(anchor='w')
        
        self.user_var = tk.StringVar()
        self.pass_var = tk.StringVar()
        
        input_frame = tk.Frame(container, bg=COLORS['primary_bg'])
        input_frame.pack(fill='x', pady=(0, 20), padx=20)

        user_entry = create_input_field(input_frame, 'Username:', self.user_var, 0, 0, 'entry')
        pass_entry = create_input_field(input_frame, 'Password:', self.pass_var, 1, 0, 'entry', mask=True)

        if user_entry:
            user_entry.bind('<Return>', self.check_login)
        if pass_entry:
            pass_entry.bind('<Return>', self.check_login)
        
        btn_frame = tk.Frame(container, bg=COLORS['primary_bg'])
        btn_frame.pack(fill='x', pady=(0, 20), padx=20)

        tk.Button(
            btn_frame,
            text='Login',
            command=self.check_login,
            font=FONTS['bold'],
            bg=COLORS['primary_accent'],
            fg=COLORS['secondary_txt']
        ).pack(fill='x')
        
        signup_frame = tk.Frame(btn_frame, bg=COLORS['primary_bg'])
        signup_frame.pack(fill='x', pady=(10, 0))
        
        tk.Label(
            signup_frame,
            text="Don't have an account? ",
            font=FONTS['small'],
            bg=COLORS['primary_bg'],
            fg=COLORS['primary_txt']
        ).pack(side='left')
        
        tk.Button(
            signup_frame,
            text="Sign Up",
            command=lambda: controller.show_view("RegisterPage"),
            font=('Verdana', 9, 'bold'),
            bg=COLORS['primary_bg'],
            fg=COLORS['primary_accent'],
            bd=0,
            cursor='hand2'
        ).pack(side='left')

        forgot_frame = tk.Frame(btn_frame, bg=COLORS['primary_bg'])
        forgot_frame.pack(fill='x', pady=(0, 20))
        tk.Button(
            forgot_frame, 
            text="Forgot Password?", 
            font=("Verdana", 9, "underline"), 
            bg=COLORS['primary_bg'], 
            fg=COLORS['primary_accent'], 
            bd=0, cursor="hand2",
            command=lambda: ForgotPasswordModal(self, self.controller)
        ).pack(side='left')
        
    def check_login(self, event=None):
        """Verify credentials and log user in."""
        user = self.user_var.get()
        pw = self.pass_var.get()
        user_id = self.controller.db.verify_user(user, pw)
        
        if user_id:
            self.user_var.set("")
            self.pass_var.set("")
            self.controller.login_success(user_id, user)
        else:
            messagebox.showerror("Login Error", "Incorrect username or password. Please try again.")

class ForgotPasswordModal(tk.Toplevel):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.title("Reset Password")

        window_width = 480
        window_height = 480
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        center_x = int(screen_width / 2 - window_width / 2)
        center_y = int(screen_height / 2 - window_height / 2)
        self.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')

        self.configure(bg=COLORS['primary_bg'])
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set() 

        self.step = 1
        self.user_id = None
        self.generated_otp = None
        self.target_email = None

        self.container = tk.Frame(self, bg=COLORS['primary_bg'], padx=20, pady=20)
        self.container.place(relx=0.5, rely=0.5, anchor='center', relwidth=0.9) 

        self.build_step_1() 

    def clear_frame(self):
        for widget in self.container.winfo_children(): widget.destroy()

    # Step 1: Enter Email
    def build_step_1(self):
        self.clear_frame()
        
        # Header
        tk.Label(self.container, text="Find Your Account", font=FONTS['header'], 
                 bg=COLORS['primary_bg'], fg=COLORS['primary_accent']).pack(pady=(0, 20), anchor='w')
        
        # Input
        form_frame = tk.Frame(self.container, bg=COLORS['primary_bg'])
        form_frame.pack(fill='x', pady=10)
        
        self.email_var = tk.StringVar()

        tk.Label(
            form_frame,
            text="Enter your email address:",
            font=FONTS['bold'],
            bg=COLORS['primary_bg'],
            fg=COLORS['primary_accent']
        ).pack(anchor='w', pady=(0, 5))

        tk.Entry(
            form_frame,
            textvariable=self.email_var,
            font=FONTS['default'],
            bg=COLORS['secondary_bg'],
            fg=COLORS['primary_txt']
        ).pack(fill='x', ipady=5)
        
        # Submit Button
        tk.Button(self.container, text="Send Code", command=self.send_otp_action,
                  bg=COLORS['primary_accent'], fg='white', font=FONTS['bold'], bd=0, pady=5).pack(fill='x', pady=20)

    def send_otp_action(self):
        email = self.email_var.get().strip()
        user = self.controller.db.get_user_by_email(email)
        
        if not user:
            messagebox.showerror("Error", "No account found with this email.")
            return

        self.user_id = user['id']
        self.target_email = email
        
        self.config(cursor="watch") 
        self.update()
        
        otp = send_reset_code(email)
        
        self.config(cursor="")
        
        if otp:
            self.generated_otp = otp
            messagebox.showinfo("Sent", f"A verification code has been sent to {email}")
            self.build_step_2()
        else:
            messagebox.showerror("Error", "Failed to send email. Check internet connection.")

    # Step 2: Verify OTP
    def build_step_2(self):
        self.clear_frame()
        
        tk.Label(self.container, text="Verify Email", font=FONTS['header'], bg=COLORS['primary_bg'], fg=COLORS['primary_accent']).pack(pady=(0, 10), anchor='w')
        tk.Label(self.container, text=f"Code sent to {self.target_email}", font=FONTS['small'], bg=COLORS['primary_bg'], fg='gray').pack(pady=(0, 20), anchor='w')
        
        form_frame = tk.Frame(self.container, bg=COLORS['primary_bg'])
        form_frame.pack(fill='x', pady=10)
        
        self.otp_var = tk.StringVar()
        
        # Label
        tk.Label(form_frame, text="Enter 6-digit Code:", font=FONTS['bold'], bg=COLORS['primary_bg'], fg=COLORS['primary_accent']).pack(anchor='w', pady=(0, 5))
        
        # Entry
        tk.Entry(form_frame, textvariable=self.otp_var, font=FONTS['default'],
                 bg=COLORS['secondary_bg'], fg=COLORS['primary_txt'], relief='flat', bd=1, highlightthickness=1).pack(fill='x', ipady=5)
        
        tk.Button(self.container, text="Verify", command=self.verify_otp_action,
                  bg=COLORS['primary_accent'], fg='white', font=FONTS['bold'], bd=0, pady=5).pack(fill='x', pady=20)

    def verify_otp_action(self):
        if self.otp_var.get().strip() == self.generated_otp:
            self.build_step_3()
        else:
            messagebox.showerror("Error", "Invalid Code.")

    # Step 3: New Password
    def build_step_3(self):
        self.clear_frame()
        
        tk.Label(self.container, text="Reset Password", font=FONTS['header'], bg=COLORS['primary_bg'], fg=COLORS['primary_accent']).pack(pady=(0, 20), anchor='w')
        
        form_frame = tk.Frame(self.container, bg=COLORS['primary_bg'])
        form_frame.pack(fill='x', pady=10)

        self.new_pass_var = tk.StringVar()
        
        # Label
        tk.Label(form_frame, text="New Password:", font=FONTS['bold'], bg=COLORS['primary_bg'], fg=COLORS['primary_accent']).pack(anchor='w', pady=(0, 5))
        
        # Entry
        tk.Entry(form_frame, textvariable=self.new_pass_var, show="*", font=FONTS['default'],
                 bg=COLORS['secondary_bg'], fg=COLORS['primary_txt'], relief='flat', bd=1, highlightthickness=1).pack(fill='x', ipady=5)
        
        tk.Button(self.container, text="Save Password", command=self.save_new_pass,
                  bg=COLORS['primary_accent'], fg='white', font=FONTS['bold'], bd=0, pady=5).pack(fill='x', pady=20)

    def save_new_pass(self):
        new_pw = self.new_pass_var.get().strip()
        if len(new_pw) < 8:
            messagebox.showwarning("Error", "Password must be at least 8 characters.")
            return

        user_data = self.controller.db.get_user_by_email(self.target_email)
        current_username = user_data['username']

        success = self.controller.db.update_credentials(self.user_id, current_username, new_pw)
        
        if success:
            messagebox.showinfo("Success", "Password reset successfully! Please login.")
            self.destroy()
        else:
            messagebox.showerror("Error", "Database error.")