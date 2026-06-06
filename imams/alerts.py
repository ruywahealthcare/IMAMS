import datetime
import customtkinter as ctk
from database import get_all_individuals
from utils import compute_individual_status, ALERT_HEX, TEST_TYPES


def get_all_alerts():
    """Return list of alert dicts for every pending item across all individuals."""
    individuals = get_all_individuals()
    alerts = []
    today = datetime.date.today()

    for ind in individuals:
        status = compute_individual_status(ind)
        name = ind['name']
        svc = ind['service_number']

        if status['monitoring_complete']:
            continue

        for ay, ay_data in status['ay_status'].items():
            for tt, ts in ay_data['tests'].items():
                if not ts['done']:
                    alerts.append({
                        'individual_id': ind['id'],
                        'service_number': svc,
                        'name': name,
                        'category': 'Test',
                        'item': f"AY{ay} {tt}",
                        'alert': ts['alert'],
                        'days_left': ts['days_left'],
                        'end_date': ay_data['end_date'],
                        'count': ts['count'],
                        'required': ts['required'],
                    })

        for med_type, ms in status['medical_status'].items():
            if not ms['done']:
                alerts.append({
                    'individual_id': ind['id'],
                    'service_number': svc,
                    'name': name,
                    'category': 'Medical',
                    'item': med_type,
                    'alert': ms['alert'],
                    'days_left': ms['days_left'],
                    'end_date': ms['end_date'],
                    'count': ms['count'],
                    'required': 1,
                })

        for num, cs in status['counselling_status'].items():
            if not cs['done']:
                alerts.append({
                    'individual_id': ind['id'],
                    'service_number': svc,
                    'name': name,
                    'category': 'Counselling',
                    'item': f"Counselling {num}",
                    'alert': cs['alert'],
                    'days_left': cs['days_left'],
                    'end_date': cs['end_date'],
                    'count': cs['count'],
                    'required': 1,
                })

    priority = {'overdue': 0, 'red': 1, 'orange': 2, 'yellow': 3, 'green': 4}
    alerts.sort(key=lambda x: (priority.get(x['alert'], 9), x['days_left']))
    return alerts


class AlertsPage(ctk.CTkFrame):
    def __init__(self, parent, on_profile_click=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.on_profile_click = on_profile_click
        self.configure(fg_color="transparent")
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="Alerts & Notifications",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(anchor="w", padx=20, pady=(20, 5))

        filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        filter_frame.pack(fill="x", padx=20, pady=5)

        self.filter_var = ctk.StringVar(value="All")
        for opt in ["All", "Overdue", "Red", "Orange", "Yellow", "Green"]:
            ctk.CTkButton(filter_frame, text=opt, width=90,
                          command=lambda o=opt: self._apply_filter(o)).pack(side="left", padx=3)

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=20, pady=10)

        self.refresh()

    def _apply_filter(self, level):
        self.filter_var.set(level)
        self.refresh()

    def refresh(self):
        for w in self.scroll.winfo_children():
            w.destroy()

        alerts = get_all_alerts()
        level = self.filter_var.get().lower()

        if level != "all":
            alerts = [a for a in alerts if a['alert'] == level]

        if not alerts:
            ctk.CTkLabel(self.scroll, text="No alerts found.",
                         font=ctk.CTkFont(size=14)).pack(pady=40)
            return

        headers = ["Service No", "Name", "Category", "Item", "Status", "Days Left", "Due Date"]
        widths = [100, 160, 100, 160, 90, 90, 110]
        hf = ctk.CTkFrame(self.scroll)
        hf.pack(fill="x", pady=(0, 2))
        for h, w in zip(headers, widths):
            ctk.CTkLabel(hf, text=h, font=ctk.CTkFont(weight="bold"),
                         width=w, anchor="w").pack(side="left", padx=4)

        for a in alerts:
            color = ALERT_HEX.get(a['alert'], '#AAAAAA')
            row = ctk.CTkFrame(self.scroll, fg_color=color + "22", corner_radius=6)
            row.pack(fill="x", pady=2)

            ind_id = a['individual_id']
            days = a['days_left']
            days_txt = f"{days}d" if days >= 0 else f"{abs(days)}d ago"
            end_d = a['end_date'].strftime('%d %b %Y') if a['end_date'] else '-'
            badge_txt = a['alert'].upper()

            vals = [a['service_number'], a['name'], a['category'],
                    a['item'], badge_txt, days_txt, end_d]
            for v, w in zip(vals, widths):
                ctk.CTkLabel(row, text=v, width=w, anchor="w",
                             text_color=color if v == badge_txt else None).pack(side="left", padx=4, pady=4)

            if self.on_profile_click:
                ctk.CTkButton(row, text="View", width=55,
                              command=lambda i=ind_id: self.on_profile_click(i)).pack(side="right", padx=8)
