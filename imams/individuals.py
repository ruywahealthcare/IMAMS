import datetime
import customtkinter as ctk
from tkinter import messagebox
import database as db
from utils import compute_individual_status, TEST_TYPES, ALERT_HEX, ALERT_BG_HEX


BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]


class IndividualsPage(ctk.CTkFrame):
    def __init__(self, parent, current_user, on_profile_click=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.current_user = current_user
        self.on_profile_click = on_profile_click
        self.configure(fg_color="transparent")
        self._build()

    def _build(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=(20, 5))
        ctk.CTkLabel(top, text="Individuals Register",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(side="left")
        ctk.CTkButton(top, text="+ Add Individual", width=140,
                      command=self._open_add).pack(side="right")

        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.pack(fill="x", padx=20, pady=5)
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._refresh_list())
        ctk.CTkEntry(search_frame, textvariable=self.search_var,
                     placeholder_text="Search by name / service no / unit...",
                     width=400).pack(side="left")

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=20, pady=10)
        self._refresh_list()

    def _refresh_list(self):
        for w in self.scroll.winfo_children():
            w.destroy()

        individuals = db.get_all_individuals()
        q = self.search_var.get().lower().strip()
        if q:
            individuals = [i for i in individuals if
                           q in i.get('name', '').lower() or
                           q in i.get('service_number', '').lower() or
                           q in i.get('unit', '').lower() or
                           q in i.get('batch', '').lower()]

        headers = ["Svc No", "Name", "Rank", "Trade", "Unit", "Batch", "Enrolled", "Alert", "Actions"]
        widths = [90, 160, 80, 80, 110, 80, 100, 80, 120]
        hf = ctk.CTkFrame(self.scroll)
        hf.pack(fill="x", pady=(0, 2))
        for h, w in zip(headers, widths):
            ctk.CTkLabel(hf, text=h, font=ctk.CTkFont(weight="bold"),
                         width=w, anchor="w").pack(side="left", padx=4)

        if not individuals:
            ctk.CTkLabel(self.scroll, text="No individuals found.",
                         font=ctk.CTkFont(size=13)).pack(pady=30)
            return

        for ind in individuals:
            status = compute_individual_status(ind)
            alert = status['overall_alert']
            color = ALERT_HEX.get(alert, '#888888')

            row = ctk.CTkFrame(self.scroll, fg_color=ALERT_BG_HEX.get(alert, '#1A2A3A'), corner_radius=6)
            row.pack(fill="x", pady=2)

            vals = [
                ind.get('service_number', ''),
                ind.get('name', ''),
                ind.get('rank', ''),
                ind.get('trade', ''),
                ind.get('unit', ''),
                ind.get('batch', ''),
                ind.get('enrollment_date', ''),
                alert.upper(),
            ]
            for v, w in zip(vals, widths):
                ctk.CTkLabel(row, text=v, width=w, anchor="w",
                             text_color=color if v == alert.upper() else None
                             ).pack(side="left", padx=4, pady=5)

            btn_frame = ctk.CTkFrame(row, fg_color="transparent")
            btn_frame.pack(side="left", padx=4)
            ind_id = ind['id']
            ctk.CTkButton(btn_frame, text="View", width=52,
                          command=lambda i=ind_id: self.on_profile_click and self.on_profile_click(i)
                          ).pack(side="left", padx=2)
            ctk.CTkButton(btn_frame, text="Edit", width=52,
                          command=lambda i=ind_id: self._open_edit(i)
                          ).pack(side="left", padx=2)
            if self.current_user.get('role') == 'admin':
                ctk.CTkButton(btn_frame, text="Del", width=42, fg_color="#c0392b",
                              hover_color="#922b21",
                              command=lambda i=ind_id, n=ind['name']: self._delete(i, n)
                              ).pack(side="left", padx=2)

    def _open_add(self):
        IndividualFormDialog(self, title="Add Individual",
                             current_user=self.current_user,
                             on_save=self._refresh_list)

    def _open_edit(self, ind_id):
        individual = db.get_individual(ind_id)
        IndividualFormDialog(self, title="Edit Individual",
                             current_user=self.current_user,
                             individual=individual,
                             on_save=self._refresh_list)

    def _delete(self, ind_id, name):
        if messagebox.askyesno("Confirm Delete",
                               f"Delete '{name}'? This also removes all tests, medical, and counselling records."):
            db.delete_individual(ind_id, self.current_user['username'])
            self._refresh_list()


class IndividualFormDialog(ctk.CTkToplevel):
    def __init__(self, parent, title, current_user, individual=None, on_save=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.current_user = current_user
        self.individual = individual
        self.on_save = on_save
        self.title(title)
        self.geometry("640x680")
        self.resizable(False, False)
        self.grab_set()
        self._build()
        if individual:
            self._populate(individual)

    def _build(self):
        ctk.CTkLabel(self, text=self.title(),
                     font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20, 10))

        form = ctk.CTkScrollableFrame(self)
        form.pack(fill="both", expand=True, padx=30, pady=5)
        self.form = form

        self.fields = {}

        def row(label, key, widget_type="entry", options=None, default=""):
            ctk.CTkLabel(form, text=label, anchor="w",
                         font=ctk.CTkFont(size=12)).pack(fill="x", pady=(8, 1))
            if widget_type == "entry":
                widget = ctk.CTkEntry(form, height=36, font=ctk.CTkFont(size=13))
                widget.pack(fill="x", pady=(0, 2))
                if default:
                    widget.insert(0, default)
                self.fields[key] = widget
            elif widget_type == "option":
                var = ctk.StringVar(value=options[0])
                ctk.CTkOptionMenu(form, variable=var, values=options,
                                  height=36, font=ctk.CTkFont(size=13)).pack(fill="x", pady=(0, 2))
                self.fields[key] = var

        row("Service Number *", "service_number")
        row("Full Name *", "name")
        row("Rank", "rank", default="AGV")
        row("Trade", "trade")
        row("Unit", "unit")
        row("Batch", "batch")
        row("Date of Birth (YYYY-MM-DD)", "date_of_birth")
        row("Enrollment Date * (YYYY-MM-DD)", "enrollment_date")
        row("Blood Group", "blood_group", "option", BLOOD_GROUPS)
        row("Mobile Number", "mobile_number")
        row("Remarks", "remarks")

        ctk.CTkButton(self, text="Save", height=40,
                      font=ctk.CTkFont(size=14, weight="bold"),
                      command=self._save).pack(pady=15)

    def _get_field_value(self, key):
        """Return the current string value for a field, regardless of widget type."""
        w = self.fields[key]
        if isinstance(w, ctk.CTkEntry):
            return w.get().strip()
        return w.get().strip()  # StringVar

    def _populate(self, ind):
        for key, widget in self.fields.items():
            val = str(ind.get(key, '') or '')
            if isinstance(widget, ctk.CTkEntry):
                widget.delete(0, "end")
                widget.insert(0, val)
            else:               # StringVar
                widget.set(val)

    def _save(self):
        data = {k: self._get_field_value(k) for k in self.fields}
        if not data['service_number'] or not data['name'] or not data['enrollment_date']:
            messagebox.showerror("Validation",
                                 "Service Number, Name, and Enrollment Date are required.\n\n"
                                 "Tip: Make sure there are no leading/trailing spaces.")
            return
        try:
            datetime.datetime.strptime(data['enrollment_date'], "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Validation", "Enrollment Date must be YYYY-MM-DD format.\nExample: 2022-06-01")
            return

        if self.individual:
            db.update_individual(self.individual['id'], data, self.current_user['username'])
        else:
            existing = db.get_individual_by_service_no(data['service_number'])
            if existing:
                messagebox.showerror("Duplicate", f"Service Number '{data['service_number']}' already exists.")
                return
            db.add_individual(data, self.current_user['username'])

        try:
            if self.on_save:
                self.on_save()
        finally:
            self.destroy()


class IndividualProfilePage(ctk.CTkFrame):
    def __init__(self, parent, individual_id, current_user, on_back=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.individual_id = individual_id
        self.current_user = current_user
        self.on_back = on_back
        self.configure(fg_color="transparent")
        self._build()

    def _build(self):
        ind = db.get_individual(self.individual_id)
        if not ind:
            ctk.CTkLabel(self, text="Individual not found.").pack(pady=40)
            return

        status = compute_individual_status(ind)
        alert = status['overall_alert']
        color = ALERT_HEX.get(alert, '#888')

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=(15, 5))
        if self.on_back:
            ctk.CTkButton(top, text="← Back", width=80,
                          command=self.on_back).pack(side="left")

        title_lbl = ctk.CTkLabel(top,
                                  text=f"{ind['name']}  ({ind['service_number']})",
                                  font=ctk.CTkFont(size=20, weight="bold"))
        title_lbl.pack(side="left", padx=20)

        badge = ctk.CTkLabel(top, text=f"  {alert.upper()}  ",
                              fg_color=color, corner_radius=8,
                              font=ctk.CTkFont(size=12, weight="bold"),
                              text_color="white")
        badge.pack(side="left")

        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.pack(fill="both", expand=True, padx=20, pady=10)

        for tab in ["Overview", "Tests", "Medical", "Counselling", "Timeline"]:
            self.tab_view.add(tab)

        self._build_overview(ind, status)
        self._build_tests(ind, status)
        self._build_medical(ind, status)
        self._build_counselling(ind, status)
        self._build_timeline(ind, status)

    def _build_overview(self, ind, status):
        tab = self.tab_view.tab("Overview")
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        fields = [
            ("Service Number", ind.get('service_number', '')),
            ("Name", ind.get('name', '')),
            ("Rank", ind.get('rank', '')),
            ("Trade", ind.get('trade', '')),
            ("Unit", ind.get('unit', '')),
            ("Batch", ind.get('batch', '')),
            ("Date of Birth", ind.get('date_of_birth', '')),
            ("Enrollment Date", ind.get('enrollment_date', '')),
            ("Blood Group", ind.get('blood_group', '')),
            ("Mobile", ind.get('mobile_number', '')),
            ("Remarks", ind.get('remarks', '')),
            ("Monitoring End",
             status['monitoring_end_date'].strftime('%d %b %Y') if status['monitoring_end_date'] else ''),
            ("Status", "Completed" if status['monitoring_complete'] else "Active"),
        ]

        for label, val in fields:
            r = ctk.CTkFrame(scroll, fg_color="transparent")
            r.pack(fill="x", pady=2)
            ctk.CTkLabel(r, text=label + ":", width=180, anchor="w",
                         font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10)
            ctk.CTkLabel(r, text=val or '-', anchor="w").pack(side="left")

    def _build_tests(self, ind, status):
        tab = self.tab_view.tab("Tests")
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        tests = db.get_tests_for_individual(ind['id'])

        for ay, ay_data in status['ay_status'].items():
            ctk.CTkLabel(scroll, text=f"Assessment Year {ay}  "
                                       f"(Window: {ay_data['start_date'].strftime('%d %b %Y')} – "
                                       f"{ay_data['end_date'].strftime('%d %b %Y')})",
                         font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(12, 4), padx=10)

            for tt in TEST_TYPES:
                ts = ay_data['tests'][tt]
                c = ALERT_HEX.get(ts['alert'], '#888')
                row = ctk.CTkFrame(scroll, fg_color=ALERT_BG_HEX.get(ts['alert'], '#1A2A3A'), corner_radius=6)
                row.pack(fill="x", padx=10, pady=2)
                ctk.CTkLabel(row, text=tt, width=80, anchor="w",
                             font=ctk.CTkFont(weight="bold")).pack(side="left", padx=8, pady=6)
                ctk.CTkLabel(row, text=f"{ts['count']}/{ts['required']} done",
                             width=100).pack(side="left")
                ctk.CTkLabel(row, text=ts['alert'].upper(), text_color=c,
                             font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10)

        ctk.CTkLabel(scroll, text="Test History",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(16, 4), padx=10)
        if not tests:
            ctk.CTkLabel(scroll, text="No test records.").pack(padx=10)
        else:
            for t in tests:
                r = ctk.CTkFrame(scroll, fg_color="transparent")
                r.pack(fill="x", padx=10, pady=1)
                ctk.CTkLabel(r, text=f"AY{t['assessment_year']} | {t['test_type']} #{t['attempt_number']} | "
                                      f"{t['date_conducted']} | {t.get('result', '') or ''} | "
                                      f"{t.get('remarks', '') or ''}",
                             anchor="w").pack(side="left")

    def _build_medical(self, ind, status):
        tab = self.tab_view.tab("Medical")
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        for med_type, ms in status['medical_status'].items():
            c = ALERT_HEX.get(ms['alert'], '#888')
            row = ctk.CTkFrame(scroll, fg_color=ALERT_BG_HEX.get(ms['alert'], '#1A2A3A'), corner_radius=6)
            row.pack(fill="x", padx=10, pady=4)
            ctk.CTkLabel(row, text=med_type, font=ctk.CTkFont(weight="bold"),
                         width=150, anchor="w").pack(side="left", padx=8, pady=6)
            ctk.CTkLabel(row, text=f"{'Done' if ms['done'] else 'Pending'}  |  "
                                    f"Window: {ms['start_date'].strftime('%d %b %Y')} – "
                                    f"{ms['end_date'].strftime('%d %b %Y')}",
                         anchor="w").pack(side="left", padx=10)
            ctk.CTkLabel(row, text=ms['alert'].upper(), text_color=c,
                         font=ctk.CTkFont(weight="bold")).pack(side="right", padx=10)

        records = db.get_medical_for_individual(ind['id'])
        ctk.CTkLabel(scroll, text="Medical History",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(16, 4), padx=10)
        if not records:
            ctk.CTkLabel(scroll, text="No medical records.").pack(padx=10)
        else:
            for r in records:
                row = ctk.CTkFrame(scroll, fg_color="transparent")
                row.pack(fill="x", padx=10, pady=1)
                ctk.CTkLabel(row, text=f"{r['medical_type']} | {r.get('date_conducted', '')} | "
                                        f"Cat: {r.get('category', '')} | {r.get('result', '')} | "
                                        f"{r.get('remarks', '')}",
                             anchor="w").pack(side="left")

    def _build_counselling(self, ind, status):
        tab = self.tab_view.tab("Counselling")
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        for num, cs in status['counselling_status'].items():
            c = ALERT_HEX.get(cs['alert'], '#888')
            row = ctk.CTkFrame(scroll, fg_color=ALERT_BG_HEX.get(cs['alert'], '#1A2A3A'), corner_radius=6)
            row.pack(fill="x", padx=10, pady=4)
            ctk.CTkLabel(row, text=f"Counselling {num}",
                         font=ctk.CTkFont(weight="bold"), width=150, anchor="w").pack(side="left", padx=8, pady=6)
            ctk.CTkLabel(row, text=f"{'Done' if cs['done'] else 'Pending'}  |  "
                                    f"Window: {cs['start_date'].strftime('%d %b %Y')} – "
                                    f"{cs['end_date'].strftime('%d %b %Y')}").pack(side="left", padx=10)
            ctk.CTkLabel(row, text=cs['alert'].upper(), text_color=c,
                         font=ctk.CTkFont(weight="bold")).pack(side="right", padx=10)

        records = db.get_counselling_for_individual(ind['id'])
        ctk.CTkLabel(scroll, text="Counselling History",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(16, 4), padx=10)
        if not records:
            ctk.CTkLabel(scroll, text="No counselling records.").pack(padx=10)
        else:
            for r in records:
                row = ctk.CTkFrame(scroll, fg_color="transparent")
                row.pack(fill="x", padx=10, pady=1)
                ctk.CTkLabel(row, text=f"C{r['counselling_number']} | {r.get('date_conducted', '')} | "
                                        f"By: {r.get('counsellor_name', '')} | {r.get('status', '')} | "
                                        f"{r.get('remarks', '')}",
                             anchor="w").pack(side="left")

    def _build_timeline(self, ind, status):
        tab = self.tab_view.tab("Timeline")
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        events = []
        tests = db.get_tests_for_individual(ind['id'])
        medical = db.get_medical_for_individual(ind['id'])
        counselling = db.get_counselling_for_individual(ind['id'])

        for t in tests:
            events.append((t['date_conducted'],
                           f"Test: AY{t['assessment_year']} {t['test_type']} #{t['attempt_number']}",
                           '#3498DB'))
        for m in medical:
            events.append((m.get('date_conducted', ''), f"Medical: {m['medical_type']}", '#27AE60'))
        for c in counselling:
            events.append((c.get('date_conducted', ''), f"Counselling {c['counselling_number']}", '#9B59B6'))

        events.sort(key=lambda x: x[0] or '0000')

        for date, label, color in events:
            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=3)
            dot = ctk.CTkLabel(row, text="●", text_color=color,
                               font=ctk.CTkFont(size=16))
            dot.pack(side="left", padx=(0, 8))
            ctk.CTkLabel(row, text=f"{date}  |  {label}", anchor="w").pack(side="left")
