"""
AAAIS - AGV ASSESSMENT ADVANCE INTIMATION SYSTEM
Entry point: Splash Screen → Login → Main Application
"""
import os
import sys
import time
import threading
import datetime
import customtkinter as ctk
from tkinter import messagebox
from PIL import Image, ImageTk

# ── Ensure local imports work ──
sys.path.insert(0, os.path.dirname(__file__))

import database as db
from database import get_setting, get_appearance, set_appearance, log_audit
from dashboard import DashboardPage
from individuals import IndividualsPage, IndividualProfilePage
from tests import TestEntryPage
from medical import MedicalEntryPage
from counselling import CounsellingEntryPage
from reports import ReportsPage
from alerts import AlertsPage
from rules import RulesPage
from settings import SettingsPage


# ─────────────────────────────────────────────────────────────
#  SPLASH SCREEN
# ─────────────────────────────────────────────────────────────

def _load_crest_ctk(size=(160, 160)):
    """Load the battalion crest as a CTkImage (HiDPI-safe)."""
    crest_path = os.path.join(os.path.dirname(__file__), 'images', 'Crest.png')
    if os.path.exists(crest_path):
        img = Image.open(crest_path).convert("RGBA").resize(size, Image.LANCZOS)
        return ctk.CTkImage(light_image=img, dark_image=img, size=size)
    return None


def _load_crest_photo(size=(140, 140)):
    """Load crest as PhotoImage (fallback for non-CTkLabel use)."""
    crest_path = os.path.join(os.path.dirname(__file__), 'images', 'Crest.png')
    if os.path.exists(crest_path):
        img = Image.open(crest_path).convert("RGBA").resize(size, Image.LANCZOS)
        return ImageTk.PhotoImage(img)
    return None


class SplashScreen(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("RUYWA")
        w, h = 700, 440
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")
        self.resizable(False, False)
        self.overrideredirect(True)

        ctk.set_appearance_mode(get_appearance('color_mode', 'dark'))

        bg_color = "#0A1628"
        self.configure(fg_color=bg_color)

        # Border frame
        border = ctk.CTkFrame(self, fg_color="#1F3864", corner_radius=0)
        border.place(x=0, y=0, relwidth=1, relheight=1)

        inner = ctk.CTkFrame(border, fg_color=bg_color, corner_radius=0)
        inner.place(x=3, y=3, relwidth=1, relheight=1)

        institute = get_setting('institute_name', 'RUYWA Battalion')
        version = get_setting('version', '1.0.0')

        # Battalion crest
        self._crest_img = _load_crest_ctk((160, 160))
        if self._crest_img:
            ctk.CTkLabel(inner, image=self._crest_img, text="").pack(pady=(30, 8))
        else:
            ctk.CTkLabel(inner, text="⚔", font=ctk.CTkFont(size=60),
                         text_color="#F1C40F").pack(pady=(30, 8))

        # Institute name
        ctk.CTkLabel(inner, text=institute,
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color="#F1C40F").pack()

        # App name
        ctk.CTkLabel(inner, text="AGV ASSESSMENT ADVANCE",
                     font=ctk.CTkFont(size=22, weight="bold"),
                     text_color="white").pack(pady=(12, 0))
        ctk.CTkLabel(inner, text=" INTIMATION SYSTEM",
                     font=ctk.CTkFont(size=22, weight="bold"),
                     text_color="white").pack()
        ctk.CTkLabel(inner, text="AAAIS",
                     font=ctk.CTkFont(size=14),
                     text_color="#3498DB").pack(pady=(4, 0))

        # Version
        ctk.CTkLabel(inner, text=f"Version {version}",
                     font=ctk.CTkFont(size=11),
                     text_color="#888888").pack(pady=(8, 0))

        # Progress bar
        self.progress = ctk.CTkProgressBar(inner, width=400, height=8,
                                           progress_color="#F1C40F")
        self.progress.set(0)
        self.progress.pack(pady=(24, 6))

        self.status_lbl = ctk.CTkLabel(inner, text="Initialising...",
                                        font=ctk.CTkFont(size=11),
                                        text_color="#888888")
        self.status_lbl.pack()

        # Animate progress
        self._duration = int(get_setting('splash_duration', '4'))
        self._progress_val = 0
        self._start_progress()

    def _start_progress(self):
        steps = 60
        interval = int(self._duration * 1000 / steps)
        messages = ["Loading database...", "Checking rules...",
                    "Computing schedules...", "Ready!"]

        def tick(step=0):
            if step > steps:
                self.destroy()
                return
            val = step / steps
            self.progress.set(val)
            msg_idx = min(int(val * len(messages)), len(messages) - 1)
            self.status_lbl.configure(text=messages[msg_idx])
            self.after(interval, tick, step + 1)

        self.after(200, tick)


# ─────────────────────────────────────────────────────────────
#  LOGIN SCREEN
# ─────────────────────────────────────────────────────────────

class LoginScreen(ctk.CTk):
    def __init__(self, on_login_success):
        super().__init__()
        self.on_login_success = on_login_success
        self.title("RUYWA – Login")
        w, h = 520, 680
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")
        self.resizable(False, False)
        self._build()

    def _build(self):
        institute = get_setting('institute_name', 'RUYWA Battalion')
        version = get_setting('version', '1.0.0')

        # Left gold accent bar
        accent = ctk.CTkFrame(self, width=8, fg_color="#F1C40F", corner_radius=0)
        accent.pack(side="left", fill="y")

        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(side="left", fill="both", expand=True, padx=36, pady=30)

        # Battalion crest
        self._crest_img = _load_crest_ctk((110, 110))
        if self._crest_img:
            ctk.CTkLabel(main, image=self._crest_img, text="").pack(pady=(10, 6))
        else:
            ctk.CTkLabel(main, text="⚔", font=ctk.CTkFont(size=50),
                         text_color="#F1C40F").pack(pady=(10, 6))

        ctk.CTkLabel(main, text=institute,
                     font=ctk.CTkFont(size=13),
                     text_color="#F1C40F").pack()

        ctk.CTkLabel(main, text="AAAIS",
                     font=ctk.CTkFont(size=28, weight="bold")).pack(pady=(8, 0))
        ctk.CTkLabel(main, text="AGV ASSESSMENT ADVANCE INTIMATION SYSTEM",
                     font=ctk.CTkFont(size=12), justify="center").pack(pady=(2, 0))

        # Login form card
        form = ctk.CTkFrame(main, corner_radius=14)
        form.pack(fill="x", pady=20)

        ctk.CTkLabel(form, text="Sign In",
                     font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(22, 14))

        ctk.CTkLabel(form, text="Username", anchor="w",
                     font=ctk.CTkFont(size=12)).pack(fill="x", padx=28, pady=(0, 2))
        self.username_entry = ctk.CTkEntry(form, placeholder_text="Enter username",
                                           height=42, font=ctk.CTkFont(size=13))
        self.username_entry.pack(fill="x", padx=28, pady=(0, 12))

        ctk.CTkLabel(form, text="Password", anchor="w",
                     font=ctk.CTkFont(size=12)).pack(fill="x", padx=28, pady=(0, 2))
        self.password_entry = ctk.CTkEntry(form, placeholder_text="Enter password",
                                           show="*", height=42, font=ctk.CTkFont(size=13))
        self.password_entry.pack(fill="x", padx=28, pady=(0, 8))
        self.password_entry.bind("<Return>", self._login)

        self.error_lbl = ctk.CTkLabel(form, text="", text_color="#E74C3C",
                                       font=ctk.CTkFont(size=11))
        self.error_lbl.pack(pady=(0, 4))

        ctk.CTkButton(form, text="LOGIN", height=44,
                      font=ctk.CTkFont(size=15, weight="bold"),
                      fg_color="#F1C40F", hover_color="#D4AC0D",
                      text_color="#0A1628",
                      command=self._login).pack(fill="x", padx=28, pady=(4, 24))

        ctk.CTkLabel(main, text=f"Version {version} • Default: admin / 12345678",
                     text_color="#555555",
                     font=ctk.CTkFont(size=10)).pack(pady=(4, 0))

    def _login(self, event=None):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if not username or not password:
            self.error_lbl.configure(text="Please enter username and password.")
            return

        user = db.authenticate_user(username, password)
        if user:
            log_audit(username, "Login", "Successful login")
            self.withdraw()
            self.on_login_success(user)
            self.destroy()
        else:
            self.error_lbl.configure(text="Invalid username or password.")
            log_audit(username, "Login Failed", "Invalid credentials")


# ─────────────────────────────────────────────────────────────
#  MAIN APPLICATION WINDOW
# ─────────────────────────────────────────────────────────────

class MainApp(ctk.CTk):
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.title("AAAIS – AGV Assessment Advance Intimation System")
        self.geometry("1280x800")
        self.minsize(1100, 650)

        # Apply saved appearance
        mode = get_appearance('color_mode', 'dark')
        ctk.set_appearance_mode(mode)

        self._nav_buttons = {}
        self._current_page = None
        self._history = []

        self._build_layout()
        self._navigate("dashboard")

        # Auto backup on start
        if get_setting('auto_backup', '1') == '1':
            self.after(3000, self._auto_backup)

    def _build_layout(self):
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#1A1A2E")
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Logo area
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="#0F3460", corner_radius=0)
        logo_frame.pack(fill="x")
        self._sidebar_crest = _load_crest_ctk((60, 60))
        if self._sidebar_crest:
            ctk.CTkLabel(logo_frame, image=self._sidebar_crest, text="").pack(pady=(12, 2))
        ctk.CTkLabel(logo_frame, text="AAAIS",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color="#F1C40F").pack(pady=(4, 0))
        ctk.CTkLabel(logo_frame, text="RUYWA Battalion",
                     font=ctk.CTkFont(size=10),
                     text_color="#AAAAAA").pack(pady=(0, 12))

        # User info
        user_frame = ctk.CTkFrame(self.sidebar, fg_color="#16213E", corner_radius=8)
        user_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(user_frame, text=f"{self.current_user['username']}",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color="white").pack(pady=(6, 0))
        ctk.CTkLabel(user_frame, text=self.current_user.get('role', 'user').upper(),
                     font=ctk.CTkFont(size=10),
                     text_color="#F1C40F").pack(pady=(0, 6))

        # Navigation
        nav_items = [
            ("Dashboard", "dashboard", "🏠"),
            ("Individuals", "individuals", "👤"),
            ("Test Entry", "tests", "✏"),
            ("Medical", "medical", "🏥"),
            ("Counselling", "counselling", "💬"),
            ("Alerts", "alerts", "🔔"),
            ("Reports", "reports", "📊"),
            ("Rules", "rules", "⚙"),
            ("Settings", "settings", "🛠"),
        ]

        nav_scroll = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent")
        nav_scroll.pack(fill="both", expand=True, padx=5, pady=5)

        for label, key, icon in nav_items:
            btn = ctk.CTkButton(nav_scroll,
                                text=f"  {icon}  {label}",
                                anchor="w",
                                height=42,
                                fg_color="transparent",
                                hover_color="#0F3460",
                                text_color="white",
                                font=ctk.CTkFont(size=13),
                                corner_radius=8,
                                command=lambda k=key: self._navigate(k))
            btn.pack(fill="x", pady=2)
            self._nav_buttons[key] = btn

        # Bottom: logout + date
        bottom = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(bottom, text=datetime.date.today().strftime("%d %b %Y"),
                     font=ctk.CTkFont(size=10), text_color="#666666").pack()
        ctk.CTkButton(bottom, text="Logout", height=34,
                      fg_color="#c0392b", hover_color="#922b21",
                      command=self._logout).pack(fill="x", pady=4)

        # Main content area
        self.content = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.content.pack(side="left", fill="both", expand=True)

        # Header bar
        self.header = ctk.CTkFrame(self.content, height=50, corner_radius=0)
        self.header.pack(fill="x")
        self.header.pack_propagate(False)
        self.header_title = ctk.CTkLabel(self.header, text="Dashboard",
                                          font=ctk.CTkFont(size=16, weight="bold"))
        self.header_title.pack(side="left", padx=20, pady=10)

        institute = get_setting('institute_name', 'RUYWA Battalion')
        ctk.CTkLabel(self.header, text=institute,
                     font=ctk.CTkFont(size=11), text_color="#888888").pack(side="right", padx=15)

        # Page container
        self.page_container = ctk.CTkFrame(self.content, fg_color="transparent")
        self.page_container.pack(fill="both", expand=True)

    def _navigate(self, page_key):
        # Clear container
        for w in self.page_container.winfo_children():
            w.destroy()

        # Update nav button highlights
        for key, btn in self._nav_buttons.items():
            btn.configure(fg_color="#0F3460" if key == page_key else "transparent")

        self._current_page = page_key
        page_titles = {
            "dashboard": "Dashboard",
            "individuals": "Individuals Register",
            "tests": "Test Entry",
            "medical": "Medical Examinations",
            "counselling": "Counselling Sessions",
            "alerts": "Alerts & Notifications",
            "reports": "Reports & Analytics",
            "rules": "Rules Management",
            "settings": "Settings",
        }
        self.header_title.configure(text=page_titles.get(page_key, page_key.title()))

        if page_key == "dashboard":
            page = DashboardPage(self.page_container,
                                  current_user=self.current_user,
                                  on_profile_click=self._open_profile)
        elif page_key == "individuals":
            page = IndividualsPage(self.page_container,
                                    current_user=self.current_user,
                                    on_profile_click=self._open_profile)
        elif page_key == "tests":
            page = TestEntryPage(self.page_container, current_user=self.current_user)
        elif page_key == "medical":
            page = MedicalEntryPage(self.page_container, current_user=self.current_user)
        elif page_key == "counselling":
            page = CounsellingEntryPage(self.page_container, current_user=self.current_user)
        elif page_key == "alerts":
            page = AlertsPage(self.page_container, on_profile_click=self._open_profile)
        elif page_key == "reports":
            page = ReportsPage(self.page_container, current_user=self.current_user)
        elif page_key == "rules":
            page = RulesPage(self.page_container, current_user=self.current_user)
        elif page_key == "settings":
            page = SettingsPage(self.page_container, current_user=self.current_user,
                                 on_theme_change=self._on_theme_change)
        else:
            page = ctk.CTkLabel(self.page_container, text=f"Page '{page_key}' not found.")

        page.pack(fill="both", expand=True)

    def _open_profile(self, individual_id: int):
        for w in self.page_container.winfo_children():
            w.destroy()
        self.header_title.configure(text="Individual Profile")

        # Deselect nav
        for btn in self._nav_buttons.values():
            btn.configure(fg_color="transparent")

        page = IndividualProfilePage(
            self.page_container,
            individual_id=individual_id,
            current_user=self.current_user,
            on_back=lambda: self._navigate("individuals")
        )
        page.pack(fill="both", expand=True)

    def _on_theme_change(self):
        pass  # ctk handles mode changes globally

    def _auto_backup(self):
        try:
            db.backup_database()
        except Exception:
            pass

    def _logout(self):
        log_audit(self.current_user['username'], "Logout", "")
        self.destroy()
        launch()


# ─────────────────────────────────────────────────────────────
#  APPLICATION LAUNCH
# ─────────────────────────────────────────────────────────────

def launch():
    """Show login, then open main app on success."""
    def on_login(user):
        app = MainApp(user)
        app.mainloop()

    login = LoginScreen(on_login_success=on_login)
    login.mainloop()


def main():
    # Initialize DB
    db.init_database()

    # Apply saved appearance before any window opens
    mode = get_appearance('color_mode', 'dark')
    ctk.set_appearance_mode(mode)
    ctk.set_default_color_theme("blue")

    # Splash screen
    splash = SplashScreen()
    splash.mainloop()

    # Then login
    launch()


if __name__ == "__main__":
    main()
