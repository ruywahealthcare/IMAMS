import sqlite3
import hashlib
import os
import shutil
import datetime
from pathlib import Path


DB_PATH = os.path.join(os.path.dirname(__file__), "imams.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def init_database():
    conn = get_connection()
    c = conn.cursor()

    c.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'user',
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now','localtime'))
    );

    CREATE TABLE IF NOT EXISTS individuals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_number TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        rank TEXT,
        trade TEXT,
        unit TEXT,
        batch TEXT,
        date_of_birth TEXT,
        enrollment_date TEXT NOT NULL,
        blood_group TEXT,
        mobile_number TEXT,
        remarks TEXT,
        status TEXT DEFAULT 'Active',
        created_at TEXT DEFAULT (datetime('now','localtime')),
        updated_at TEXT DEFAULT (datetime('now','localtime'))
    );

    CREATE TABLE IF NOT EXISTS tests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        individual_id INTEGER NOT NULL,
        test_type TEXT NOT NULL,
        attempt_number INTEGER NOT NULL,
        assessment_year INTEGER NOT NULL,
        date_conducted TEXT NOT NULL,
        result TEXT,
        remarks TEXT,
        entered_by TEXT,
        created_at TEXT DEFAULT (datetime('now','localtime')),
        FOREIGN KEY (individual_id) REFERENCES individuals(id)
    );

    CREATE TABLE IF NOT EXISTS medical_examinations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        individual_id INTEGER NOT NULL,
        medical_type TEXT NOT NULL,
        date_conducted TEXT,
        category TEXT,
        result TEXT,
        remarks TEXT,
        entered_by TEXT,
        created_at TEXT DEFAULT (datetime('now','localtime')),
        FOREIGN KEY (individual_id) REFERENCES individuals(id)
    );

    CREATE TABLE IF NOT EXISTS counselling_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        individual_id INTEGER NOT NULL,
        counselling_number INTEGER NOT NULL,
        date_conducted TEXT,
        counsellor_name TEXT,
        remarks TEXT,
        status TEXT,
        entered_by TEXT,
        created_at TEXT DEFAULT (datetime('now','localtime')),
        FOREIGN KEY (individual_id) REFERENCES individuals(id)
    );

    CREATE TABLE IF NOT EXISTS rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rule_key TEXT UNIQUE NOT NULL,
        rule_value TEXT NOT NULL,
        description TEXT,
        updated_by TEXT,
        updated_at TEXT DEFAULT (datetime('now','localtime'))
    );

    CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        action TEXT NOT NULL,
        details TEXT,
        timestamp TEXT DEFAULT (datetime('now','localtime'))
    );

    CREATE TABLE IF NOT EXISTS app_settings (
        key TEXT PRIMARY KEY,
        value TEXT
    );

    CREATE TABLE IF NOT EXISTS appearance_settings (
        key TEXT PRIMARY KEY,
        value TEXT
    );
    """)

    # Default admin user
    c.execute("SELECT id FROM users WHERE username='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                  ('admin', hash_password('12345678'), 'admin'))

    # Default rules
    default_rules = [
        ('monitoring_period_months', '48', 'Total monitoring period in months'),
        ('min_test_gap_days', '30', 'Minimum gap between same tests (days)'),
        ('alert_yellow_days', '150', 'Yellow alert threshold (days)'),
        ('alert_orange_days', '120', 'Orange alert threshold (days)'),
        ('alert_red_days', '90', 'Red alert threshold (days)'),
        ('ay2_start_month', '7', 'Assessment Year 2 start month'),
        ('ay2_end_month', '18', 'Assessment Year 2 end month'),
        ('ay3_start_month', '19', 'Assessment Year 3 start month'),
        ('ay3_end_month', '30', 'Assessment Year 3 end month'),
        ('ay4_start_month', '31', 'Assessment Year 4 start month'),
        ('ay4_end_month', '42', 'Assessment Year 4 end month'),
        ('annual_medical_start_month', '25', 'Annual medical start month'),
        ('annual_medical_end_month', '30', 'Annual medical end month'),
        ('exit_medical_start_month', '42', 'Exit medical start month'),
        ('exit_medical_end_month', '45', 'Exit medical end month'),
        ('counselling1_start_month', '19', 'Counselling 1 start month'),
        ('counselling1_end_month', '24', 'Counselling 1 end month'),
        ('counselling2_start_month', '31', 'Counselling 2 start month'),
        ('counselling2_end_month', '36', 'Counselling 2 end month'),
        ('tests_per_year', '2', 'Number of tests per assessment year'),
    ]
    for key, val, desc in default_rules:
        c.execute("INSERT OR IGNORE INTO rules (rule_key, rule_value, description) VALUES (?,?,?)",
                  (key, val, desc))

    # Default app settings
    defaults = [
        ('institute_name', 'RUYWA Batallion'),
        ('unit_name', 'HQ Unit'),
        ('org_name', 'Organisation'),
        ('address', 'Address Line 1, City'),
        ('contact', '+91-XXXXXXXXXX'),
        ('version', '1.0.0'),
        ('splash_duration', '4'),
        ('backup_location', os.path.join(os.path.dirname(__file__), 'backups')),
        ('theme', 'dark'),
        ('auto_backup', '1'),
    ]
    for k, v in defaults:
        c.execute("INSERT OR IGNORE INTO app_settings (key, value) VALUES (?,?)", (k, v))

    conn.commit()
    conn.close()


def get_rule(key: str, default=None):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT rule_value FROM rules WHERE rule_key=?", (key,))
    row = c.fetchone()
    conn.close()
    if row:
        try:
            return int(row[0])
        except ValueError:
            return row[0]
    return default


def get_setting(key: str, default=None):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT value FROM app_settings WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else default


def set_setting(key: str, value: str):
    conn = get_connection()
    conn.execute("INSERT OR REPLACE INTO app_settings (key, value) VALUES (?,?)", (key, value))
    conn.commit()
    conn.close()


def get_appearance(key: str, default=None):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT value FROM appearance_settings WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else default


def set_appearance(key: str, value: str):
    conn = get_connection()
    conn.execute("INSERT OR REPLACE INTO appearance_settings (key, value) VALUES (?,?)", (key, value))
    conn.commit()
    conn.close()


def log_audit(username: str, action: str, details: str = ""):
    conn = get_connection()
    conn.execute("INSERT INTO audit_log (username, action, details) VALUES (?,?,?)",
                 (username, action, details))
    conn.commit()
    conn.close()


def authenticate_user(username: str, password: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password_hash=? AND is_active=1",
              (username, hash_password(password)))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


# ──────────────── Individual CRUD ────────────────

def add_individual(data: dict, username: str) -> int:
    conn = get_connection()
    c = conn.cursor()
    c.execute("""INSERT INTO individuals
        (service_number, name, rank, trade, unit, batch, date_of_birth,
         enrollment_date, blood_group, mobile_number, remarks)
        VALUES (:service_number,:name,:rank,:trade,:unit,:batch,:date_of_birth,
                :enrollment_date,:blood_group,:mobile_number,:remarks)""", data)
    new_id = c.lastrowid
    conn.commit()
    conn.close()
    log_audit(username, "Added Individual", f"Service No: {data['service_number']}, Name: {data['name']}")
    return new_id


def update_individual(individual_id: int, data: dict, username: str):
    conn = get_connection()
    data['id'] = individual_id
    data['updated_at'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn.execute("""UPDATE individuals SET
        service_number=:service_number, name=:name, rank=:rank, trade=:trade,
        unit=:unit, batch=:batch, date_of_birth=:date_of_birth,
        enrollment_date=:enrollment_date, blood_group=:blood_group,
        mobile_number=:mobile_number, remarks=:remarks, updated_at=:updated_at
        WHERE id=:id""", data)
    conn.commit()
    conn.close()
    log_audit(username, "Updated Individual", f"ID: {individual_id}")


def delete_individual(individual_id: int, username: str):
    row = None
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("SELECT service_number, name FROM individuals WHERE id=?", (individual_id,))
        row = c.fetchone()
        # Remove dependent child records first to satisfy FK constraints
        c.execute("DELETE FROM tests WHERE individual_id=?", (individual_id,))
        c.execute("DELETE FROM medical_examinations WHERE individual_id=?", (individual_id,))
        c.execute("DELETE FROM counselling_sessions WHERE individual_id=?", (individual_id,))
        c.execute("DELETE FROM individuals WHERE id=?", (individual_id,))
        conn.commit()
    finally:
        conn.close()
    if row:
        log_audit(username, "Deleted Individual", f"Service No: {row[0]}, Name: {row[1]}")


def get_all_individuals():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM individuals ORDER BY name")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def get_individual(individual_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM individuals WHERE id=?", (individual_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def get_individual_by_service_no(svc_no: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM individuals WHERE service_number=?", (svc_no,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


# ──────────────── Tests ────────────────

def add_test(data: dict, username: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""INSERT INTO tests
        (individual_id, test_type, attempt_number, assessment_year, date_conducted, result, remarks, entered_by)
        VALUES (:individual_id,:test_type,:attempt_number,:assessment_year,:date_conducted,:result,:remarks,:entered_by)""",
              {**data, 'entered_by': username})
    conn.commit()
    conn.close()
    log_audit(username, "Added Test", f"IndID:{data['individual_id']} Type:{data['test_type']} Attempt:{data['attempt_number']}")


def get_tests_for_individual(individual_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM tests WHERE individual_id=? ORDER BY date_conducted", (individual_id,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def get_latest_test(individual_id: int, test_type: str, assessment_year: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""SELECT * FROM tests WHERE individual_id=? AND test_type=? AND assessment_year=?
                 ORDER BY date_conducted DESC LIMIT 1""",
              (individual_id, test_type, assessment_year))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def get_test_count(individual_id: int, test_type: str, assessment_year: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM tests WHERE individual_id=? AND test_type=? AND assessment_year=?",
              (individual_id, test_type, assessment_year))
    count = c.fetchone()[0]
    conn.close()
    return count


# ──────────────── Medical ────────────────

def add_medical(data: dict, username: str):
    conn = get_connection()
    conn.execute("""INSERT INTO medical_examinations
        (individual_id, medical_type, date_conducted, category, result, remarks, entered_by)
        VALUES (:individual_id,:medical_type,:date_conducted,:category,:result,:remarks,:entered_by)""",
                 {**data, 'entered_by': username})
    conn.commit()
    conn.close()
    log_audit(username, "Added Medical", f"IndID:{data['individual_id']} Type:{data['medical_type']}")


def get_medical_for_individual(individual_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM medical_examinations WHERE individual_id=? ORDER BY date_conducted",
              (individual_id,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def get_medical_count(individual_id: int, medical_type: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM medical_examinations WHERE individual_id=? AND medical_type=?",
              (individual_id, medical_type))
    count = c.fetchone()[0]
    conn.close()
    return count


# ──────────────── Counselling ────────────────

def add_counselling(data: dict, username: str):
    conn = get_connection()
    conn.execute("""INSERT INTO counselling_sessions
        (individual_id, counselling_number, date_conducted, counsellor_name, remarks, status, entered_by)
        VALUES (:individual_id,:counselling_number,:date_conducted,:counsellor_name,:remarks,:status,:entered_by)""",
                 {**data, 'entered_by': username})
    conn.commit()
    conn.close()
    log_audit(username, "Added Counselling", f"IndID:{data['individual_id']} No:{data['counselling_number']}")


def get_counselling_for_individual(individual_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM counselling_sessions WHERE individual_id=? ORDER BY date_conducted",
              (individual_id,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def get_counselling_count(individual_id: int, counselling_number: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM counselling_sessions WHERE individual_id=? AND counselling_number=?",
              (individual_id, counselling_number))
    count = c.fetchone()[0]
    conn.close()
    return count


# ──────────────── Rules ────────────────

def get_all_rules():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM rules ORDER BY rule_key")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def update_rule(rule_key: str, value: str, username: str):
    conn = get_connection()
    conn.execute("""UPDATE rules SET rule_value=?, updated_by=?,
                    updated_at=datetime('now','localtime') WHERE rule_key=?""",
                 (value, username, rule_key))
    conn.commit()
    conn.close()
    log_audit(username, "Updated Rule", f"Key:{rule_key} Value:{value}")


# ──────────────── Audit ────────────────

def get_audit_logs(limit=500):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


# ──────────────── Backup / Restore ────────────────

def backup_database(backup_dir: str = None):
    if not backup_dir:
        backup_dir = get_setting('backup_location',
                                 os.path.join(os.path.dirname(__file__), 'backups'))
    os.makedirs(backup_dir, exist_ok=True)
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    dest = os.path.join(backup_dir, f"imams_backup_{ts}.db")
    shutil.copy2(DB_PATH, dest)
    return dest


def restore_database(backup_path: str):
    shutil.copy2(backup_path, DB_PATH)


# ──────────────── User Management ────────────────

def get_all_users():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, username, role, is_active, created_at FROM users ORDER BY username")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def create_user(username: str, password: str, role: str, admin_user: str):
    conn = get_connection()
    conn.execute("INSERT INTO users (username, password_hash, role) VALUES (?,?,?)",
                 (username, hash_password(password), role))
    conn.commit()
    conn.close()
    log_audit(admin_user, "Created User", f"Username:{username} Role:{role}")


def update_user_password(user_id: int, new_password: str, admin_user: str):
    conn = get_connection()
    conn.execute("UPDATE users SET password_hash=? WHERE id=?",
                 (hash_password(new_password), user_id))
    conn.commit()
    conn.close()
    log_audit(admin_user, "Reset Password", f"UserID:{user_id}")


def toggle_user_active(user_id: int, is_active: int, admin_user: str):
    conn = get_connection()
    conn.execute("UPDATE users SET is_active=? WHERE id=?", (is_active, user_id))
    conn.commit()
    conn.close()
    log_audit(admin_user, "Toggled User", f"UserID:{user_id} Active:{is_active}")
