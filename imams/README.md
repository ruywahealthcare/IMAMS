# AAAIS — AGV ASSESSMENT ADVANCE INTIMATION SYSTEM

A complete offline desktop application for Windows 10/11 built with Python + CustomTkinter.

---

## Quick Start

### 1. Install Python 3.10 or later (Windows)
Download from https://www.python.org/downloads/

### 2. Install dependencies
Open Command Prompt in this folder and run:
```
pip install -r requirements.txt
```

### 3. Launch the application
```
python main.py
```

---

## Default Login
| Field    | Value      |
|----------|------------|
| Username | `admin`    |
| Password | `12345678` |

Change your password immediately from **Settings → Change Password**.

---

## Features

| Module | Description |
|---|---|
| Dashboard | Summary cards, command bar search, quick filters |
| Individuals | Full CRUD, per-individual profile with tabs |
| Test Entry | Firing / DST / BPET / PPT — with 30-day gap enforcement |
| Medical | Annual Medical & Exit Medical tracking |
| Counselling | Counselling 1 & 2 session tracking |
| Alerts | Green / Yellow / Orange / Red / Overdue alert engine |
| Reports | PDF, Excel, CSV export for 12+ report types |
| Rules | Edit all monitoring rules without changing code |
| Settings | Themes, user management, backup/restore, audit log |

---

## Assessment Year Structure

| AY | Period | Tests Required |
|----|--------|---------------|
| AY1 | Month 0–18 | None (Regimental Centre, read-only) |
| AY2 | Month 7–18 | Firing×2, DST×2, BPET×2, PPT×2 |
| AY3 | Month 19–30 | Firing×2, DST×2, BPET×2, PPT×2 |
| AY4 | Month 31–42 | Firing×2, DST×2, BPET×2, PPT×2 |

---

## Alert Engine

| Colour | Threshold |
|--------|-----------|
| 🟢 Green | Requirement completed |
| 🟡 Yellow | Due within 150 days |
| 🟠 Orange | Due within 120 days |
| 🔴 Red | Due within 90 days |
| 🟣 Overdue | Window expired without completion |

All thresholds are editable in **Rules Management**.

---

## Command Bar Examples

Type any of these in the Dashboard search bar:

```
show overdue
show red alerts
show orange alerts
show yellow alerts
show completed
show firing pending
show dst pending
show bpet pending
show ppt pending
show medical pending
show counselling pending
show annual medical due
show exit medical due
show all individuals due in next 90 days
show batch 2024
show unit HQ
show service no 12345
show name Kumar
```

---

## Backup Location
Default: `imams/backups/` folder.  
Configurable from **Settings → Backup & Restore**.

---

## File Structure

```
imams/
├── main.py           — Entry point (Splash → Login → App)
├── database.py       — SQLite CRUD + schema init
├── utils.py          — Schedule calculations & alert logic
├── dashboard.py      — Dashboard + command bar
├── individuals.py    — Individual records management
├── tests.py          — Test entry module
├── medical.py        — Medical examination module
├── counselling.py    — Counselling session module
├── alerts.py         — Alerts page
├── reports.py        — PDF / Excel / CSV reports
├── rules.py          — Rules management
├── settings.py       — Settings, themes, users, audit log
├── requirements.txt  — Python dependencies
└── imams.db          — SQLite database (auto-created)
```

---

## Build Standalone EXE (optional)

To create a single Windows executable:
```
pip install pyinstaller
pyinstaller --onefile --windowed --name IMAMS main.py
```
The EXE will appear in `dist/IMAMS.exe`.
