import customtkinter as ctk
from tkinter import messagebox
import database as db


RULE_LABELS = {
    'monitoring_period_months': 'Monitoring Period (months)',
    'min_test_gap_days': 'Min Gap Between Tests (days)',
    'alert_yellow_days': 'Yellow Alert Threshold (days)',
    'alert_orange_days': 'Orange Alert Threshold (days)',
    'alert_red_days': 'Red Alert Threshold (days)',
    'ay2_start_month': 'AY2 Start Month',
    'ay2_end_month': 'AY2 End Month',
    'ay3_start_month': 'AY3 Start Month',
    'ay3_end_month': 'AY3 End Month',
    'ay4_start_month': 'AY4 Start Month',
    'ay4_end_month': 'AY4 End Month',
    'annual_medical_start_month': 'Annual Medical Start Month',
    'annual_medical_end_month': 'Annual Medical End Month',
    'exit_medical_start_month': 'Exit Medical Start Month',
    'exit_medical_end_month': 'Exit Medical End Month',
    'counselling1_start_month': 'Counselling 1 Start Month',
    'counselling1_end_month': 'Counselling 1 End Month',
    'counselling2_start_month': 'Counselling 2 Start Month',
    'counselling2_end_month': 'Counselling 2 End Month',
    'tests_per_year': 'Tests Required per AY',
}

# Sensible upper bounds so values stay realistic
RULE_MAX = {
    'monitoring_period_months': 600,
    'min_test_gap_days': 3650,
    'alert_yellow_days': 3650,
    'alert_orange_days': 3650,
    'alert_red_days': 3650,
    'tests_per_year': 50,
}
DEFAULT_MAX = 600  # months-style fields


class IntSpinbox(ctk.CTkFrame):
    """Number-only input with up/down arrows. Accepts integers only."""

    def __init__(self, parent, width=150, height=34, min_val=0, max_val=999, step=1, **kwargs):
        super().__init__(parent, width=width, height=height, fg_color="transparent", **kwargs)
        self.min_val = min_val
        self.max_val = max_val
        self.step = step

        self.grid_columnconfigure(1, weight=1)
        vcmd = (self.register(self._validate), '%P')

        self.minus_btn = ctk.CTkButton(self, text="\u2212", width=32, height=height,
                                       command=self._decrement)
        self.minus_btn.grid(row=0, column=0, padx=(0, 2))

        self.entry = ctk.CTkEntry(self, width=58, height=height, justify="center",
                                  validate="key", validatecommand=vcmd)
        self.entry.grid(row=0, column=1, padx=2, sticky="ew")

        self.plus_btn = ctk.CTkButton(self, text="+", width=32, height=height,
                                      command=self._increment)
        self.plus_btn.grid(row=0, column=2, padx=(2, 0))

    def _validate(self, proposed):
        if proposed == "":
            return True
        return proposed.isdigit()

    def _increment(self):
        self.set(min(self.get() + self.step, self.max_val))

    def _decrement(self):
        self.set(max(self.get() - self.step, self.min_val))

    def get(self):
        try:
            return int(self.entry.get())
        except (ValueError, TypeError):
            return self.min_val

    def set(self, value):
        self.entry.delete(0, "end")
        self.entry.insert(0, str(value))

    def set_enabled(self, enabled):
        state = "normal" if enabled else "disabled"
        self.entry.configure(state=state)
        self.minus_btn.configure(state=state)
        self.plus_btn.configure(state=state)


class RulesPage(ctk.CTkFrame):
    def __init__(self, parent, current_user, **kwargs):
        super().__init__(parent, **kwargs)
        self.current_user = current_user
        self.configure(fg_color="transparent")
        self.is_admin = current_user.get('role') == 'admin'
        self.entries = {}
        self._build()

    def _build(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=(20, 5))
        ctk.CTkLabel(top, text="Rules Management",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(side="left")
        if self.is_admin:
            ctk.CTkButton(top, text="Save All Changes", width=160,
                          command=self._save_all).pack(side="right")

        ctk.CTkLabel(self, text="Modify monitoring rules. Changes apply immediately to all calculations.",
                     text_color="#888888", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=20)

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=10)

        rules = db.get_all_rules()
        rule_dict = {r['rule_key']: r for r in rules}

        for key, label in RULE_LABELS.items():
            rule = rule_dict.get(key, {})
            value = rule.get('rule_value', '0')
            description = rule.get('description', '')

            row = ctk.CTkFrame(scroll, corner_radius=8)
            row.pack(fill="x", pady=4)

            info_col = ctk.CTkFrame(row, fg_color="transparent")
            info_col.pack(side="left", fill="x", expand=True, padx=15, pady=10)
            ctk.CTkLabel(info_col, text=label, anchor="w",
                         font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w")
            if description:
                ctk.CTkLabel(info_col, text=description, anchor="w",
                             text_color="#888888", font=ctk.CTkFont(size=11)).pack(anchor="w")

            spin = IntSpinbox(row, min_val=0, max_val=RULE_MAX.get(key, DEFAULT_MAX))
            try:
                spin.set(int(value))
            except (ValueError, TypeError):
                spin.set(0)
            spin.pack(side="right", padx=15, pady=10)
            if not self.is_admin:
                spin.set_enabled(False)
            self.entries[key] = spin

    def _save_all(self):
        for key, spin in self.entries.items():
            db.update_rule(key, str(spin.get()), self.current_user['username'])
        messagebox.showinfo("Saved", "All rules updated successfully.\nChanges are effective immediately.")
