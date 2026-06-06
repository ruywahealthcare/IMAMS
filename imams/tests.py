import datetime
import customtkinter as ctk
from tkinter import messagebox
import database as db
from utils import TEST_TYPES, ASSESSMENT_YEARS, get_assessment_year_windows, compute_individual_status, ALERT_HEX, to_display_date, to_iso_date


class TestEntryPage(ctk.CTkFrame):
    def __init__(self, parent, current_user, **kwargs):
        super().__init__(parent, **kwargs)
        self.current_user = current_user
        self.configure(fg_color="transparent")
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="Test Entry",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(anchor="w", padx=20, pady=(20, 5))

        form = ctk.CTkFrame(self)
        form.pack(fill="x", padx=20, pady=10)

        left = ctk.CTkFrame(form, fg_color="transparent")
        left.grid(row=0, column=0, padx=20, pady=10, sticky="nw")
        right = ctk.CTkFrame(form, fg_color="transparent")
        right.grid(row=0, column=1, padx=20, pady=10, sticky="nw")

        def lbl(parent, text):
            ctk.CTkLabel(parent, text=text, anchor="w").pack(fill="x", pady=(6, 0))

        lbl(left, "Service Number *")
        self.svc_entry = ctk.CTkEntry(left, width=220)
        self.svc_entry.pack(fill="x")
        self.svc_entry.bind("<FocusOut>", self._on_svc_lookup)

        self.name_lbl = ctk.CTkLabel(left, text="", text_color="#27AE60")
        self.name_lbl.pack(anchor="w")

        lbl(left, "Test Type *")
        self.test_type_var = ctk.StringVar(value=TEST_TYPES[0])
        ctk.CTkOptionMenu(left, variable=self.test_type_var, values=TEST_TYPES).pack(fill="x")

        lbl(left, "Assessment Year *")
        self.ay_var = ctk.StringVar(value="2")
        ctk.CTkOptionMenu(left, variable=self.ay_var, values=["2", "3", "4"]).pack(fill="x")

        lbl(left, "Attempt Number *")
        self.attempt_var = ctk.StringVar(value="1")
        ctk.CTkOptionMenu(left, variable=self.attempt_var, values=["1", "2"]).pack(fill="x")

        lbl(right, "Date Conducted * (DD-MM-YYYY)")
        self.date_entry = ctk.CTkEntry(right, width=220)
        self.date_entry.insert(0, datetime.date.today().strftime('%d-%m-%Y'))
        self.date_entry.pack(fill="x")

        lbl(right, "Result")
        self.result_var = ctk.StringVar(value="Pass")
        ctk.CTkOptionMenu(right, variable=self.result_var,
                          values=["Pass", "Fail", "Absent", "Pending"]).pack(fill="x")

        lbl(right, "Remarks")
        self.remarks_entry = ctk.CTkEntry(right, width=220)
        self.remarks_entry.pack(fill="x")

        ctk.CTkButton(self, text="Submit Test Entry", width=200,
                      command=self._submit).pack(pady=15)

        ctk.CTkLabel(self, text="Recent Test Entries",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", padx=20, pady=(10, 0))
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent", height=300)
        self.scroll.pack(fill="both", expand=True, padx=20, pady=5)
        self._refresh_recent()

    def _on_svc_lookup(self, event=None):
        svc = self.svc_entry.get().strip()
        ind = db.get_individual_by_service_no(svc)
        if ind:
            self.name_lbl.configure(text=f"\u2713 {ind['name']} ({ind.get('rank', '')})",
                                    text_color="#27AE60")
            self._ind_id = ind['id']
        else:
            self.name_lbl.configure(text="Individual not found", text_color="#E74C3C")
            self._ind_id = None

    def _submit(self):
        self._on_svc_lookup()
        if not hasattr(self, '_ind_id') or not self._ind_id:
            messagebox.showerror("Error", "Valid Service Number required.")
            return

        ind = db.get_individual(self._ind_id)
        test_type = self.test_type_var.get()
        attempt = int(self.attempt_var.get())
        ay = int(self.ay_var.get())
        date_str = self.date_entry.get().strip()

        try:
            date_obj = datetime.datetime.strptime(date_str, "%d-%m-%Y").date()
        except ValueError:
            messagebox.showerror("Error", "Date must be DD-MM-YYYY.\nExample: 01-06-2022")
            return

        date_iso = date_obj.strftime("%Y-%m-%d")

        min_gap = db.get_rule('min_test_gap_days', 30)
        prev = db.get_latest_test(self._ind_id, test_type, ay)
        if prev:
            prev_date = datetime.datetime.strptime(prev['date_conducted'], "%Y-%m-%d").date()
            gap = (date_obj - prev_date).days
            if gap < min_gap:
                messagebox.showerror("Gap Violation",
                                     f"Minimum gap is {min_gap} days. "
                                     f"Previous {test_type} was on "
                                     f"{to_display_date(prev['date_conducted'])} ({gap} days ago).")
                return

        count = db.get_test_count(self._ind_id, test_type, ay)
        tests_per_year = db.get_rule('tests_per_year', 2)
        if count >= tests_per_year:
            messagebox.showerror("Limit Reached",
                                 f"{test_type} already has {count}/{tests_per_year} entries for AY{ay}.")
            return

        data = {
            'individual_id': self._ind_id,
            'test_type': test_type,
            'attempt_number': attempt,
            'assessment_year': ay,
            'date_conducted': date_iso,
            'result': self.result_var.get(),
            'remarks': self.remarks_entry.get().strip(),
        }
        db.add_test(data, self.current_user['username'])
        messagebox.showinfo("Success", f"{test_type} entry saved.")
        self._refresh_recent()

    def _refresh_recent(self):
        for w in self.scroll.winfo_children():
            w.destroy()

        import sqlite3
        conn = db.get_connection()
        c = conn.cursor()
        c.execute("""SELECT t.*, i.name, i.service_number
                     FROM tests t JOIN individuals i ON t.individual_id=i.id
                     ORDER BY t.created_at DESC LIMIT 50""")
        rows = [dict(r) for r in c.fetchall()]
        conn.close()

        headers = ["Svc No", "Name", "AY", "Test", "Attempt", "Date", "Result", "Remarks"]
        widths = [90, 160, 40, 80, 70, 100, 70, 160]
        hf = ctk.CTkFrame(self.scroll)
        hf.pack(fill="x")
        for h, w in zip(headers, widths):
            ctk.CTkLabel(hf, text=h, font=ctk.CTkFont(weight="bold"),
                         width=w, anchor="w").pack(side="left", padx=4)

        for r in rows:
            row = ctk.CTkFrame(self.scroll, fg_color="transparent")
            row.pack(fill="x", pady=1)
            vals = [r.get('service_number', ''), r.get('name', ''),
                    f"AY{r['assessment_year']}", r['test_type'],
                    f"#{r['attempt_number']}", to_display_date(r['date_conducted']),
                    r.get('result', ''), r.get('remarks', '')]
            for v, w in zip(vals, widths):
                ctk.CTkLabel(row, text=v, width=w, anchor="w").pack(side="left", padx=4, pady=3)
