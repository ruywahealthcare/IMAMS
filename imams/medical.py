import datetime
import customtkinter as ctk
from tkinter import messagebox
import database as db


MEDICAL_TYPES = ["Annual Medical", "Exit Medical"]
MEDICAL_CATEGORIES = ["SHAPE-1", "SHAPE-2", "SHAPE-3", "Low Medical", "Unfit", "Other"]


class MedicalEntryPage(ctk.CTkFrame):
    def __init__(self, parent, current_user, **kwargs):
        super().__init__(parent, **kwargs)
        self.current_user = current_user
        self.configure(fg_color="transparent")
        self._ind_id = None
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="Medical Examination Entry",
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

        lbl(left, "Medical Type *")
        self.med_type_var = ctk.StringVar(value=MEDICAL_TYPES[0])
        ctk.CTkOptionMenu(left, variable=self.med_type_var, values=MEDICAL_TYPES).pack(fill="x")

        lbl(right, "Date Conducted * (YYYY-MM-DD)")
        self.date_entry = ctk.CTkEntry(right, width=220)
        self.date_entry.insert(0, datetime.date.today().strftime('%Y-%m-%d'))
        self.date_entry.pack(fill="x")

        lbl(right, "Medical Category")
        self.cat_var = ctk.StringVar(value=MEDICAL_CATEGORIES[0])
        ctk.CTkOptionMenu(right, variable=self.cat_var, values=MEDICAL_CATEGORIES).pack(fill="x")

        lbl(right, "Result")
        self.result_var = ctk.StringVar(value="Fit")
        ctk.CTkOptionMenu(right, variable=self.result_var,
                          values=["Fit", "Unfit", "Temporary Unfit", "Referred"]).pack(fill="x")

        lbl(right, "Remarks")
        self.remarks_entry = ctk.CTkEntry(right, width=220)
        self.remarks_entry.pack(fill="x")

        ctk.CTkButton(self, text="Save Medical Entry", width=200,
                      command=self._submit).pack(pady=15)

        ctk.CTkLabel(self, text="Recent Medical Records",
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

        med_type = self.med_type_var.get()
        existing_count = db.get_medical_count(self._ind_id, med_type)
        if existing_count >= 1:
            if not messagebox.askyesno("Duplicate Warning",
                                        f"{med_type} record already exists. Add another?"):
                return

        data = {
            'individual_id': self._ind_id,
            'medical_type': med_type,
            'date_conducted': date_str,
            'category': self.cat_var.get(),
            'result': self.result_var.get(),
            'remarks': self.remarks_entry.get().strip(),
        }
        db.add_medical(data, self.current_user['username'])
        messagebox.showinfo("Success", "Medical record saved.")
        self._refresh_recent()

    def _refresh_recent(self):
        for w in self.scroll.winfo_children():
            w.destroy()

        conn = db.get_connection()
        c = conn.cursor()
        c.execute("""SELECT m.*, i.name, i.service_number
                     FROM medical_examinations m JOIN individuals i ON m.individual_id=i.id
                     ORDER BY m.created_at DESC LIMIT 50""")
        rows = [dict(r) for r in c.fetchall()]
        conn.close()

        headers = ["Svc No", "Name", "Type", "Date", "Category", "Result", "Remarks"]
        widths = [90, 160, 130, 100, 110, 90, 180]
        hf = ctk.CTkFrame(self.scroll)
        hf.pack(fill="x")
        for h, w in zip(headers, widths):
            ctk.CTkLabel(hf, text=h, font=ctk.CTkFont(weight="bold"),
                         width=w, anchor="w").pack(side="left", padx=4)

        for r in rows:
            row = ctk.CTkFrame(self.scroll, fg_color="transparent")
            row.pack(fill="x", pady=1)
            vals = [r.get('service_number', ''), r.get('name', ''), r['medical_type'],
                    r.get('date_conducted', ''), r.get('category', ''),
                    r.get('result', ''), r.get('remarks', '')]
            for v, w in zip(vals, widths):
                ctk.CTkLabel(row, text=v, width=w, anchor="w").pack(side="left", padx=4, pady=3)
