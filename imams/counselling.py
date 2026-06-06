import datetime
import customtkinter as ctk
from tkinter import messagebox
import database as db


class CounsellingEntryPage(ctk.CTkFrame):
    def __init__(self, parent, current_user, **kwargs):
        super().__init__(parent, **kwargs)
        self.current_user = current_user
        self.configure(fg_color="transparent")
        self._ind_id = None
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="Counselling Entry",
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
        self.svc_entry.bind("<FocusOut>", self._lookup)

        self.name_lbl = ctk.CTkLabel(left, text="", text_color="#27AE60")
        self.name_lbl.pack(anchor="w")

        lbl(left, "Counselling Number *")
        self.num_var = ctk.StringVar(value="1")
        ctk.CTkOptionMenu(left, variable=self.num_var, values=["1", "2"]).pack(fill="x")

        lbl(right, "Date Conducted * (YYYY-MM-DD)")
        self.date_entry = ctk.CTkEntry(right, width=220)
        self.date_entry.insert(0, datetime.date.today().strftime('%Y-%m-%d'))
        self.date_entry.pack(fill="x")

        lbl(right, "Counsellor Name *")
        self.counsellor_entry = ctk.CTkEntry(right, width=220)
        self.counsellor_entry.pack(fill="x")

        lbl(right, "Status")
        self.status_var = ctk.StringVar(value="Completed")
        ctk.CTkOptionMenu(right, variable=self.status_var,
                          values=["Completed", "Pending", "Rescheduled", "Cancelled"]).pack(fill="x")

        lbl(right, "Remarks")
        self.remarks_entry = ctk.CTkEntry(right, width=220)
        self.remarks_entry.pack(fill="x")

        ctk.CTkButton(self, text="Save Counselling Entry", width=200,
                      command=self._submit).pack(pady=15)

        ctk.CTkLabel(self, text="Recent Counselling Records",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", padx=20, pady=(5, 0))
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent", height=280)
        self.scroll.pack(fill="both", expand=True, padx=20, pady=5)
        self._refresh_recent()

    def _lookup(self, event=None):
        svc = self.svc_entry.get().strip()
        ind = db.get_individual_by_service_no(svc)
        if ind:
            self.name_lbl.configure(text=f"✓ {ind['name']}", text_color="#27AE60")
            self._ind_id = ind['id']
        else:
            self.name_lbl.configure(text="Not found", text_color="#E74C3C")
            self._ind_id = None

    def _submit(self):
        self._lookup()
        if not self._ind_id:
            messagebox.showerror("Error", "Valid Service Number required.")
            return
        date_str = self.date_entry.get().strip()
        try:
            datetime.datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Error", "Date must be YYYY-MM-DD.")
            return
        if not self.counsellor_entry.get().strip():
            messagebox.showerror("Error", "Counsellor Name is required.")
            return

        num = int(self.num_var.get())
        existing = db.get_counselling_count(self._ind_id, num)
        if existing >= 1:
            if not messagebox.askyesno("Duplicate Warning",
                                        f"Counselling {num} already recorded. Add another?"):
                return

        data = {
            'individual_id': self._ind_id,
            'counselling_number': num,
            'date_conducted': date_str,
            'counsellor_name': self.counsellor_entry.get().strip(),
            'remarks': self.remarks_entry.get().strip(),
            'status': self.status_var.get(),
        }
        db.add_counselling(data, self.current_user['username'])
        messagebox.showinfo("Success", f"Counselling {num} entry saved.")
        self._refresh_recent()

    def _refresh_recent(self):
        for w in self.scroll.winfo_children():
            w.destroy()

        conn = db.get_connection()
        c = conn.cursor()
        c.execute("""SELECT cs.*, i.name, i.service_number
                     FROM counselling_sessions cs JOIN individuals i ON cs.individual_id=i.id
                     ORDER BY cs.created_at DESC LIMIT 50""")
        rows = [dict(r) for r in c.fetchall()]
        conn.close()

        headers = ["Svc No", "Name", "C#", "Date", "Counsellor", "Status", "Remarks"]
        widths = [90, 160, 40, 100, 160, 100, 160]
        hf = ctk.CTkFrame(self.scroll)
        hf.pack(fill="x")
        for h, w in zip(headers, widths):
            ctk.CTkLabel(hf, text=h, font=ctk.CTkFont(weight="bold"),
                         width=w, anchor="w").pack(side="left", padx=4)

        for r in rows:
            row = ctk.CTkFrame(self.scroll, fg_color="transparent")
            row.pack(fill="x", pady=1)
            vals = [r.get('service_number', ''), r.get('name', ''),
                    str(r['counselling_number']), r.get('date_conducted', ''),
                    r.get('counsellor_name', ''), r.get('status', ''), r.get('remarks', '')]
            for v, w in zip(vals, widths):
                ctk.CTkLabel(row, text=v, width=w, anchor="w").pack(side="left", padx=4, pady=3)
