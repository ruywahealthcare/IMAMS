import os
import customtkinter as ctk
from tkinter import messagebox, filedialog, colorchooser
import database as db


THEMES = {
    "Dark": {"mode": "dark", "color": "#1F6AA5"},
    "Light": {"mode": "light", "color": "#1F6AA5"},
    "Military Green": {"mode": "dark", "color": "#4E6B44"},
    "Indian Army": {"mode": "dark", "color": "#556B2F"},
    "Navy": {"mode": "dark", "color": "#1B3A6B"},
    "Air Force": {"mode": "light", "color": "#003087"},
    "Professional Blue": {"mode": "dark", "color": "#003366"},
}


class SettingsPage(ctk.CTkFrame):
    def __init__(self, parent, current_user, on_theme_change=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.current_user = current_user
        self.on_theme_change = on_theme_change
        self.is_admin = current_user.get('role') == 'admin'
        self.configure(fg_color="transparent")
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="Settings",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(anchor="w", padx=20, pady=(20, 5))

        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(fill="both", expand=True, padx=20, pady=10)

        for tab in ["General", "Appearance", "Backup & Restore", "User Management",
                    "Audit Log", "Change Password"]:
            self.tabs.add(tab)

        self._build_general()
        self._build_appearance()
        self._build_backup()
        self._build_users()
        self._build_audit()
        self._build_password()

    # ──── General ────
    def _build_general(self):
        tab = self.tabs.tab("General")
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        self.gen_fields = {}
        fields = [
            ('institute_name', 'Institute Name'),
            ('unit_name', 'Unit Name'),
            ('org_name', 'Organisation Name'),
            ('address', 'Address'),
            ('contact', 'Contact Details'),
            ('version', 'Version'),
            ('splash_duration', 'Splash Screen Duration (sec)'),
        ]

        for key, label in fields:
            ctk.CTkLabel(scroll, text=label, anchor="w",
                         font=ctk.CTkFont(weight="bold")).pack(fill="x", padx=10, pady=(8, 0))
            var = ctk.StringVar(value=db.get_setting(key, ''))
            ctk.CTkEntry(scroll, textvariable=var,
                         state="normal" if self.is_admin else "disabled").pack(fill="x", padx=10)
            self.gen_fields[key] = var

        if self.is_admin:
            ctk.CTkButton(scroll, text="Save General Settings",
                          command=self._save_general).pack(pady=15, padx=10)

    def _save_general(self):
        for key, var in self.gen_fields.items():
            db.set_setting(key, var.get().strip())
        db.log_audit(self.current_user['username'], "Updated Settings", "General settings")
        messagebox.showinfo("Saved", "General settings saved.")

    # ──── Appearance ────
    def _build_appearance(self):
        tab = self.tabs.tab("Appearance")
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        if not self.is_admin:
            ctk.CTkLabel(scroll, text="Only administrators can modify appearance settings.",
                         text_color="#E74C3C").pack(pady=20)
            return

        ctk.CTkLabel(scroll, text="Theme",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 4))

        theme_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        theme_frame.pack(fill="x", padx=10)
        for theme_name in THEMES.keys():
            ctk.CTkButton(theme_frame, text=theme_name, width=130,
                          command=lambda t=theme_name: self._apply_theme(t)).pack(side="left", padx=4, pady=4)

        ctk.CTkLabel(scroll, text="Color Mode",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(12, 4))
        mode_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        mode_frame.pack(fill="x", padx=10)
        ctk.CTkButton(mode_frame, text="Light Mode", width=130,
                      command=lambda: self._set_mode("light")).pack(side="left", padx=4)
        ctk.CTkButton(mode_frame, text="Dark Mode", width=130,
                      command=lambda: self._set_mode("dark")).pack(side="left", padx=4)

        ctk.CTkLabel(scroll, text="Accent Color",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(12, 4))
        ctk.CTkButton(scroll, text="Pick Accent Color",
                      command=self._pick_color).pack(anchor="w", padx=10)

        ctk.CTkLabel(scroll, text="Font Size",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(12, 4))
        self.font_size_var = ctk.StringVar(value=db.get_appearance('font_size', '13'))
        font_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        font_frame.pack(fill="x", padx=10)
        for sz in ["11", "12", "13", "14", "15", "16"]:
            ctk.CTkButton(font_frame, text=sz, width=55,
                          command=lambda s=sz: self._set_font_size(s)).pack(side="left", padx=3)

        ctk.CTkLabel(scroll, text="Background Image",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(12, 4))
        bg_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        bg_frame.pack(fill="x", padx=10)
        ctk.CTkButton(bg_frame, text="Upload Dashboard BG", width=180,
                      command=lambda: self._upload_bg('dashboard')).pack(side="left", padx=4)
        ctk.CTkButton(bg_frame, text="Upload Login BG", width=160,
                      command=lambda: self._upload_bg('login')).pack(side="left", padx=4)
        ctk.CTkButton(bg_frame, text="Remove BG Images", width=160,
                      command=self._remove_bg, fg_color="#c0392b").pack(side="left", padx=4)

    def _apply_theme(self, theme_name):
        t = THEMES[theme_name]
        ctk.set_appearance_mode(t['mode'])
        ctk.set_default_color_theme("blue")
        db.set_appearance('theme', theme_name)
        db.set_appearance('color_mode', t['mode'])
        db.log_audit(self.current_user['username'], "Changed Theme", theme_name)
        if self.on_theme_change:
            self.on_theme_change()

    def _set_mode(self, mode):
        ctk.set_appearance_mode(mode)
        db.set_appearance('color_mode', mode)

    def _pick_color(self):
        color = colorchooser.askcolor(title="Pick Accent Color")
        if color and color[1]:
            db.set_appearance('accent_color', color[1])
            messagebox.showinfo("Saved", f"Accent color set to {color[1]}.\nRestart to fully apply.")

    def _set_font_size(self, size):
        db.set_appearance('font_size', size)
        messagebox.showinfo("Saved", f"Font size set to {size}.\nRestart to fully apply.")

    def _upload_bg(self, page):
        fp = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.png *.webp *.jpeg")])
        if fp:
            import shutil
            dest_dir = os.path.join(os.path.dirname(__file__), 'assets')
            os.makedirs(dest_dir, exist_ok=True)
            ext = os.path.splitext(fp)[1]
            dest = os.path.join(dest_dir, f"bg_{page}{ext}")
            shutil.copy2(fp, dest)
            db.set_appearance(f"bg_{page}", dest)
            messagebox.showinfo("Saved", f"Background image set for {page} page.")

    def _remove_bg(self):
        for page in ['dashboard', 'login']:
            db.set_appearance(f"bg_{page}", '')
        messagebox.showinfo("Removed", "Background images removed.")

    # ──── Backup & Restore ────
    def _build_backup(self):
        tab = self.tabs.tab("Backup & Restore")
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        ctk.CTkLabel(scroll, text="Backup Location",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(15, 4))
        self.backup_dir_var = ctk.StringVar(
            value=db.get_setting('backup_location', os.path.join(os.path.dirname(__file__), 'backups')))
        row = ctk.CTkFrame(scroll, fg_color="transparent")
        row.pack(fill="x", padx=10)
        ctk.CTkEntry(row, textvariable=self.backup_dir_var, width=400).pack(side="left", padx=5)
        ctk.CTkButton(row, text="Browse", width=80,
                      command=self._browse_backup_dir).pack(side="left")

        ctk.CTkButton(scroll, text="Backup Database Now", width=200,
                      command=self._do_backup).pack(anchor="w", padx=10, pady=15)

        ctk.CTkSeparator = ctk.CTkFrame(scroll, height=1, fg_color="#444444")
        ctk.CTkSeparator.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(scroll, text="Restore Database",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 4))
        ctk.CTkLabel(scroll, text="WARNING: Restoring will overwrite all current data.",
                     text_color="#E74C3C").pack(anchor="w", padx=10)
        ctk.CTkButton(scroll, text="Select Backup to Restore", width=220,
                      fg_color="#c0392b", hover_color="#922b21",
                      command=self._do_restore).pack(anchor="w", padx=10, pady=10)

    def _browse_backup_dir(self):
        d = filedialog.askdirectory()
        if d:
            self.backup_dir_var.set(d)
            db.set_setting('backup_location', d)

    def _do_backup(self):
        backup_dir = self.backup_dir_var.get()
        dest = db.backup_database(backup_dir)
        db.log_audit(self.current_user['username'], "Backup", f"Saved to: {dest}")
        messagebox.showinfo("Backup Complete", f"Backup saved:\n{dest}")

    def _do_restore(self):
        fp = filedialog.askopenfilename(filetypes=[("SQLite DB", "*.db")])
        if fp:
            if messagebox.askyesno("Confirm Restore",
                                   "This will overwrite all current data. Are you sure?"):
                db.restore_database(fp)
                db.log_audit(self.current_user['username'], "Restore", f"From: {fp}")
                messagebox.showinfo("Restored", "Database restored. Please restart the application.")

    # ──── User Management ────
    def _build_users(self):
        tab = self.tabs.tab("User Management")

        if not self.is_admin:
            ctk.CTkLabel(tab, text="Only administrators can manage users.",
                         text_color="#E74C3C").pack(pady=20)
            return

        top = ctk.CTkFrame(tab, fg_color="transparent")
        top.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(top, text="Users",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(side="left")
        ctk.CTkButton(top, text="+ Add User", width=110,
                      command=self._add_user).pack(side="right")

        self.users_scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent", height=300)
        self.users_scroll.pack(fill="both", expand=True, padx=10)
        self._refresh_users()

    def _refresh_users(self):
        for w in self.users_scroll.winfo_children():
            w.destroy()

        users = db.get_all_users()
        headers = ["ID", "Username", "Role", "Active", "Created At", "Actions"]
        widths = [40, 140, 80, 60, 160, 200]
        hf = ctk.CTkFrame(self.users_scroll)
        hf.pack(fill="x")
        for h, w in zip(headers, widths):
            ctk.CTkLabel(hf, text=h, font=ctk.CTkFont(weight="bold"),
                         width=w, anchor="w").pack(side="left", padx=4)

        for u in users:
            row = ctk.CTkFrame(self.users_scroll, fg_color="transparent")
            row.pack(fill="x", pady=2)
            vals = [str(u['id']), u['username'], u['role'],
                    "Yes" if u['is_active'] else "No", u.get('created_at', '')]
            for v, w in zip(vals, widths):
                ctk.CTkLabel(row, text=v, width=w, anchor="w").pack(side="left", padx=4, pady=4)

            uid = u['id']
            uname = u['username']
            btn_frame = ctk.CTkFrame(row, fg_color="transparent")
            btn_frame.pack(side="left")
            ctk.CTkButton(btn_frame, text="Reset Pwd", width=90,
                          command=lambda i=uid: self._reset_password(i)).pack(side="left", padx=2)
            if u['username'] != 'admin':
                state = 0 if u['is_active'] else 1
                lbl = "Disable" if u['is_active'] else "Enable"
                ctk.CTkButton(btn_frame, text=lbl, width=70,
                              command=lambda i=uid, s=state: self._toggle_user(i, s)).pack(side="left", padx=2)

    def _add_user(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Add User")
        dialog.geometry("360x280")
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Add New User",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20, 10))

        fields = {}
        for label, key in [("Username", "username"), ("Password", "password"), ("Role", "role")]:
            ctk.CTkLabel(dialog, text=label).pack(anchor="w", padx=20)
            if key == "role":
                var = ctk.StringVar(value="user")
                ctk.CTkOptionMenu(dialog, variable=var, values=["user", "admin"]).pack(fill="x", padx=20)
            else:
                var = ctk.StringVar()
                ctk.CTkEntry(dialog, textvariable=var,
                             show="*" if key == "password" else "").pack(fill="x", padx=20)
            fields[key] = var

        def do_create():
            uname = fields['username'].get().strip()
            pwd = fields['password'].get().strip()
            role = fields['role'].get()
            if not uname or not pwd:
                messagebox.showerror("Error", "Username and Password required.", parent=dialog)
                return
            try:
                db.create_user(uname, pwd, role, self.current_user['username'])
                messagebox.showinfo("Created", f"User '{uname}' created.", parent=dialog)
                dialog.destroy()
                self._refresh_users()
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=dialog)

        ctk.CTkButton(dialog, text="Create User", command=do_create).pack(pady=15)

    def _reset_password(self, user_id):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Reset Password")
        dialog.geometry("320x200")
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="New Password").pack(pady=(20, 4))
        pwd_var = ctk.StringVar()
        ctk.CTkEntry(dialog, textvariable=pwd_var, show="*").pack(fill="x", padx=20)

        def do_reset():
            pwd = pwd_var.get().strip()
            if not pwd:
                messagebox.showerror("Error", "Password cannot be empty.", parent=dialog)
                return
            db.update_user_password(user_id, pwd, self.current_user['username'])
            messagebox.showinfo("Done", "Password reset successfully.", parent=dialog)
            dialog.destroy()

        ctk.CTkButton(dialog, text="Reset", command=do_reset).pack(pady=15)

    def _toggle_user(self, user_id, new_state):
        db.toggle_user_active(user_id, new_state, self.current_user['username'])
        self._refresh_users()

    # ──── Audit Log ────
    def _build_audit(self):
        tab = self.tabs.tab("Audit Log")

        top = ctk.CTkFrame(tab, fg_color="transparent")
        top.pack(fill="x", padx=10, pady=8)
        ctk.CTkLabel(top, text="Audit Log",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(side="left")
        ctk.CTkButton(top, text="Refresh", width=90,
                      command=self._refresh_audit).pack(side="right")
        ctk.CTkButton(top, text="Export CSV", width=100,
                      command=self._export_audit).pack(side="right", padx=5)

        self.audit_scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        self.audit_scroll.pack(fill="both", expand=True, padx=10)
        self._refresh_audit()

    def _refresh_audit(self):
        for w in self.audit_scroll.winfo_children():
            w.destroy()

        logs = db.get_audit_logs(500)
        headers = ["#", "User", "Action", "Details", "Timestamp"]
        widths = [40, 100, 150, 300, 150]
        hf = ctk.CTkFrame(self.audit_scroll)
        hf.pack(fill="x")
        for h, w in zip(headers, widths):
            ctk.CTkLabel(hf, text=h, font=ctk.CTkFont(weight="bold"),
                         width=w, anchor="w").pack(side="left", padx=4)

        for log in logs:
            row = ctk.CTkFrame(self.audit_scroll, fg_color="transparent")
            row.pack(fill="x", pady=1)
            vals = [str(log['id']), log.get('username', ''), log['action'],
                    log.get('details', ''), log.get('timestamp', '')]
            for v, w in zip(vals, widths):
                ctk.CTkLabel(row, text=str(v)[:60], width=w, anchor="w").pack(side="left", padx=4, pady=3)

    def _export_audit(self):
        from tkinter import filedialog
        import csv
        fp = filedialog.asksaveasfilename(defaultextension=".csv",
                                          initialfile="IMAMS_AuditLog",
                                          filetypes=[("CSV", "*.csv")])
        if fp:
            logs = db.get_audit_logs(10000)
            with open(fp, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['id', 'username', 'action', 'details', 'timestamp'])
                writer.writeheader()
                writer.writerows(logs)
            messagebox.showinfo("Exported", f"Audit log saved:\n{fp}")

    # ──── Change Password ────
    def _build_password(self):
        tab = self.tabs.tab("Change Password")

        ctk.CTkLabel(tab, text="Change My Password",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20, 10))

        self.cp_fields = {}
        for label, key in [("Current Password", "current"), ("New Password", "new"),
                            ("Confirm New Password", "confirm")]:
            ctk.CTkLabel(tab, text=label).pack(anchor="w", padx=30, pady=(6, 0))
            var = ctk.StringVar()
            ctk.CTkEntry(tab, textvariable=var, show="*", width=280).pack(padx=30)
            self.cp_fields[key] = var

        ctk.CTkButton(tab, text="Update Password", width=180,
                      command=self._change_password).pack(pady=20)

    def _change_password(self):
        current = self.cp_fields['current'].get()
        new = self.cp_fields['new'].get()
        confirm = self.cp_fields['confirm'].get()

        if not current or not new or not confirm:
            messagebox.showerror("Error", "All fields are required.")
            return
        if new != confirm:
            messagebox.showerror("Error", "New passwords do not match.")
            return
        if len(new) < 6:
            messagebox.showerror("Error", "Password must be at least 6 characters.")
            return

        # Verify current password
        user = db.authenticate_user(self.current_user['username'], current)
        if not user:
            messagebox.showerror("Error", "Current password is incorrect.")
            return

        db.update_user_password(self.current_user['id'], new, self.current_user['username'])
        db.log_audit(self.current_user['username'], "Changed Password", "Self password change")
        messagebox.showinfo("Success", "Password updated successfully.")
        for v in self.cp_fields.values():
            v.set('')
