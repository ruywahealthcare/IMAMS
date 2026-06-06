import customtkinter as ctk
from utils import get_dashboard_summary, search_individuals, compute_individual_status, ALERT_HEX, ALERT_BG_HEX, TEST_TYPES, to_display_date
import database as db


ALERT_COLORS = {
    'green': '#27AE60',
    'yellow': '#F1C40F',
    'orange': '#E67E22',
    'red': '#E74C3C',
    'overdue': '#8E44AD',
}

CARD_CONFIGS = [
    ("Total", "total", "#2C3E50"),
    ("Active", "active", "#2980B9"),
    ("Yellow (150d)", "yellow", "#F39C12"),
    ("Orange (120d)", "orange", "#E67E22"),
    ("Red (90d)", "red", "#E74C3C"),
    ("Overdue", "overdue", "#8E44AD"),
    ("Completed", "completed", "#27AE60"),
]


class DashboardPage(ctk.CTkFrame):
    def __init__(self, parent, current_user, on_profile_click=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.current_user = current_user
        self.on_profile_click = on_profile_click
        self.configure(fg_color="transparent")
        self._build()

    def _build(self):
        # Command bar
        cmd_frame = ctk.CTkFrame(self, corner_radius=10)
        cmd_frame.pack(fill="x", padx=20, pady=(15, 5))
        ctk.CTkLabel(cmd_frame, text="Search:", width=60,
                     font=ctk.CTkFont(size=13)).pack(side="left", padx=(15, 5), pady=8)
        self.cmd_var = ctk.StringVar()
        self.cmd_entry = ctk.CTkEntry(cmd_frame, textvariable=self.cmd_var,
                                      placeholder_text="Type a command or name (e.g. 'show overdue', 'show red alerts', 'John')",
                                      font=ctk.CTkFont(size=13), height=36)
        self.cmd_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.cmd_entry.bind("<Return>", self._run_search)
        ctk.CTkButton(cmd_frame, text="Search", width=90,
                      command=self._run_search).pack(side="left", padx=5)
        ctk.CTkButton(cmd_frame, text="Clear", width=70,
                      command=self._clear_search).pack(side="left", padx=(0, 10))

        # Summary cards
        self.cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.cards_frame.pack(fill="x", padx=20, pady=10)

        self.card_labels = {}
        for i, (label, key, color) in enumerate(CARD_CONFIGS):
            card = ctk.CTkFrame(self.cards_frame, fg_color=color, corner_radius=12, width=120, height=80)
            card.grid(row=0, column=i, padx=6, pady=4, sticky="nsew")
            card.grid_propagate(False)
            self.cards_frame.grid_columnconfigure(i, weight=1)

            ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=11),
                         text_color="white").place(relx=0.5, rely=0.28, anchor="center")
            num_lbl = ctk.CTkLabel(card, text="0", font=ctk.CTkFont(size=28, weight="bold"),
                                   text_color="white")
            num_lbl.place(relx=0.5, rely=0.65, anchor="center")
            self.card_labels[key] = num_lbl

        # Filter buttons
        filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        filter_frame.pack(fill="x", padx=20, pady=(5, 0))
        ctk.CTkLabel(filter_frame, text="Filter:",
                     font=ctk.CTkFont(size=12)).pack(side="left")

        filters = [("All", "all"), ("Overdue", "overdue"), ("Red", "red"),
                   ("Orange", "orange"), ("Yellow", "yellow"), ("Completed", "completed")]
        for label, key in filters:
            ctk.CTkButton(filter_frame, text=label, width=85,
                          command=lambda k=key: self._quick_filter(k)).pack(side="left", padx=3, pady=4)

        # Test detail area
        detail_frame = ctk.CTkFrame(self, fg_color="transparent")
        detail_frame.pack(fill="x", padx=20, pady=(0, 5))
        ctk.CTkLabel(detail_frame, text="Tests:",
                     font=ctk.CTkFont(size=12)).pack(side="left")
        for tt in TEST_TYPES:
            ctk.CTkButton(detail_frame, text=tt, width=80,
                          command=lambda t=tt: self._filter_test(t)).pack(side="left", padx=3)
        for mt in ["Annual Medical", "Exit Medical"]:
            ctk.CTkButton(detail_frame, text=mt, width=130,
                          command=lambda m=mt: self._filter_medical(m)).pack(side="left", padx=3)

        # Results table
        ctk.CTkLabel(self, text="Individuals",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", padx=20, pady=(8, 2))

        self.result_label = ctk.CTkLabel(self, text="", text_color="#888888",
                                         font=ctk.CTkFont(size=11))
        self.result_label.pack(anchor="w", padx=20)

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=20, pady=(4, 10))

        self.refresh()

    def refresh(self):
        summary = get_dashboard_summary()
        for key, lbl in self.card_labels.items():
            lbl.configure(text=str(summary.get(key, 0)))
        self._show_all()

    def _show_all(self):
        individuals = db.get_all_individuals()
        results = []
        for ind in individuals:
            status = compute_individual_status(ind)
            results.append({**ind, 'status': status})
        self._render_results(results, f"All individuals ({len(results)})")

    def _quick_filter(self, key):
        individuals = db.get_all_individuals()
        results = []
        for ind in individuals:
            status = compute_individual_status(ind)
            match = False
            if key == 'all':
                match = True
            elif key == 'completed':
                match = status['monitoring_complete']
            else:
                match = status['overall_alert'] == key
            if match:
                results.append({**ind, 'status': status})
        self._render_results(results, f"{key.capitalize()} ({len(results)})")

    def _filter_test(self, test_type):
        individuals = db.get_all_individuals()
        results = []
        for ind in individuals:
            status = compute_individual_status(ind)
            for ay, ay_data in status['ay_status'].items():
                ts = ay_data['tests'].get(test_type)
                if ts and not ts['done']:
                    results.append({**ind, 'status': status})
                    break
        self._render_results(results, f"{test_type} Pending ({len(results)})")

    def _filter_medical(self, med_type):
        individuals = db.get_all_individuals()
        results = []
        for ind in individuals:
            status = compute_individual_status(ind)
            ms = status['medical_status'].get(med_type)
            if ms and not ms['done']:
                results.append({**ind, 'status': status})
        self._render_results(results, f"{med_type} Pending ({len(results)})")

    def _run_search(self, event=None):
        query = self.cmd_var.get().strip()
        if not query:
            self._show_all()
            return
        results = search_individuals(query)
        self._render_results(results, f"Results for '{query}' ({len(results)} found)")

    def _clear_search(self):
        self.cmd_var.set('')
        self._show_all()

    def _render_results(self, results: list, label: str):
        self.result_label.configure(text=label)
        for w in self.scroll.winfo_children():
            w.destroy()

        if not results:
            ctk.CTkLabel(self.scroll, text="No records match.",
                         font=ctk.CTkFont(size=13)).pack(pady=30)
            return

        headers = ["Svc No", "Name", "Rank", "COY", "Batch", "Enrolled", "Status", "Alert", ""]
        widths = [90, 160, 70, 110, 80, 100, 80, 80, 80]
        hf = ctk.CTkFrame(self.scroll)
        hf.pack(fill="x")
        for h, w in zip(headers, widths):
            ctk.CTkLabel(hf, text=h, font=ctk.CTkFont(weight="bold"),
                         width=w, anchor="w").pack(side="left", padx=3)

        for item in results:
            ind = item
            status = item.get('status') or compute_individual_status(item)
            alert = status['overall_alert']
            color = ALERT_COLORS.get(alert, '#888')

            row = ctk.CTkFrame(self.scroll, fg_color=ALERT_BG_HEX.get(alert, '#1A2A3A'), corner_radius=6)
            row.pack(fill="x", pady=2)

            state_txt = "Completed" if status['monitoring_complete'] else "Active"
            vals = [
                ind.get('service_number', ''), ind.get('name', ''), ind.get('rank', ''),
                ind.get('coy', ''), ind.get('batch', ''), to_display_date(ind.get('enrollment_date', '')),
                state_txt, alert.upper()
            ]
            for v, w in zip(vals, widths):
                ctk.CTkLabel(row, text=v, width=w, anchor="w",
                             text_color=color if v == alert.upper() else None
                             ).pack(side="left", padx=3, pady=5)

            if self.on_profile_click:
                ind_id = ind['id']
                ctk.CTkButton(row, text="Profile", width=70,
                              command=lambda i=ind_id: self.on_profile_click(i)).pack(side="left", padx=5)
