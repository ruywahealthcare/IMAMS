# IMAMS — Individual Monitoring & Assessment Management System

  A standalone desktop application built with **Python + CustomTkinter** for Windows 10/11.

  ## Features

  - **Dashboard** — colour-coded alert overview (green / yellow / orange / red) per individual
  - **Individual Management** — add, edit, delete personnel records
  - **Test Records** — Firing, DST and other assessments with gap & attempt-count enforcement
  - **Medical Records** — Annual Medical, Pre-employment, and specialist entries
  - **Counselling Log** — record up to 3 counselling sessions per individual
  - **Reports** — export to Excel / PDF
  - **Settings** — manage users, rules thresholds, appearance

  ## Default Login

  | Field    | Value      |
  |----------|------------|
  | Username | `admin`    |
  | Password | `12345678` |

  ## Quick Start (Windows)

  ```bat
  install.bat      # creates venv and installs packages
  run_imams.bat    # launches the application
  ```

  ## Requirements

  See `imams/requirements.txt`. Python 3.11+ required.

  ## Stack

  - Python 3.11 · CustomTkinter 5.x · SQLite · OpenPyXL · ReportLab
  