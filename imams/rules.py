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
            value = rule.get('rule_value', '')
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

            var = ctk.StringVar(value=str(value))
            entry = ctk.CTkEntry(row, textvariable=var, width=120,
                                 state="normal" if self.is_admin else "disabled")
            entry.pack(side="right", padx=15, pady=10)
            self.entries[key] = var

    def _save_all(self):
        errors = []
        for key, var in self.entries.items():
            val = var.get().strip()
            try:
                int(val)
            except ValueError:
                errors.append(f"{RULE_LABELS.get(key, key)}: must be an integer")

        if errors:
            messagebox.showerror("Validation Errors", "\n".join(errors))
            return

        for key, var in self.entries.items():
            db.update_rule(key, var.get().strip(), self.current_user['username'])

        messagebox.showinfo("Saved", "All rules updated successfully.\nChanges are effective immediately.")
