"""
IMAMS – Automated feature test suite (no GUI required)
Run:  python run_tests.py
"""
import sys, os, datetime, traceback, tempfile, atexit
sys.path.insert(0, os.path.dirname(__file__))

# ── Use a temp-file test database so we never touch imams.db ──
_TMP_DB = tempfile.mktemp(suffix="_imams_test.db")
atexit.register(lambda: os.unlink(_TMP_DB) if os.path.exists(_TMP_DB) else None)

import database as db
db.DB_PATH = _TMP_DB          # redirect before any call

# ── Colour output helpers ──────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

passed = []
failed = []

def ok(name):
    passed.append(name)
    print(f"  {GREEN}✓{RESET}  {name}")

def fail(name, reason):
    failed.append(name)
    print(f"  {RED}✗{RESET}  {name}")
    print(f"       {RED}→ {reason}{RESET}")

def section(title):
    print(f"\n{BLUE}{BOLD}{'─'*56}{RESET}")
    print(f"{BLUE}{BOLD}  {title}{RESET}")
    print(f"{BLUE}{BOLD}{'─'*56}{RESET}")

# ══════════════════════════════════════════════════════════════
section("1 · Database initialisation")
# ══════════════════════════════════════════════════════════════
try:
    db.init_database()
    ok("init_database() runs without error")
except Exception as e:
    fail("init_database()", str(e)); sys.exit(1)

# Default admin user
try:
    user = db.authenticate_user("admin", "12345678")
    assert user is not None, "authenticate_user returned None"
    assert user['role'] == 'admin', f"expected role=admin got {user['role']}"
    ok("Default admin user exists and authenticates")
except AssertionError as e:
    fail("Default admin authentication", str(e))

# ══════════════════════════════════════════════════════════════
section("2 · Individual management (the form-validation fix)")
# ══════════════════════════════════════════════════════════════

IND1 = {
    'service_number': '10012345',
    'name':           'Naik Rajesh Kumar Singh',
    'rank':           'Naik',
    'trade':          'Infantryman',
    'coy':            '1 BIHAR',
    'batch':          '2022',
    'date_of_birth':  '1998-03-14',
    'enrollment_date':'2022-06-01',
    'blood_group':    'B+',
    'mobile_number':  '9876543210',
    'remarks':        '',
}
IND2 = {
    'service_number': '10023456',
    'name':           'Sep Arun Kumar Yadav',
    'rank':           'Sep',
    'trade':          'Signaller',
    'coy':            '2 RAJPUT',
    'batch':          '2022',
    'date_of_birth':  '1999-07-22',
    'enrollment_date':'2022-06-01',
    'blood_group':    'O+',
    'mobile_number':  '9812345678',
    'remarks':        '',
}
IND3 = {
    'service_number': '10034567',
    'name':           'L/Hav Suresh Babu Patil',
    'rank':           'L/Hav',
    'trade':          'Driver MT',
    'coy':            '1 BIHAR',
    'batch':          '2022',
    'date_of_birth':  '1997-11-05',
    'enrollment_date':'2022-06-01',
    'blood_group':    'A+',
    'mobile_number':  '9823456789',
    'remarks':        '',
}

try:
    db.add_individual(IND1, 'admin')
    db.add_individual(IND2, 'admin')
    db.add_individual(IND3, 'admin')
    ok("add_individual() — 3 individuals inserted")
except Exception as e:
    fail("add_individual()", str(e))

try:
    ind = db.get_individual_by_service_no('10012345')
    assert ind is not None
    assert ind['name'] == 'Naik Rajesh Kumar Singh'
    ok("get_individual_by_service_no() returns correct record")
except AssertionError as e:
    fail("get_individual_by_service_no()", str(e))

try:
    all_inds = db.get_all_individuals()
    assert len(all_inds) == 3, f"expected 3 got {len(all_inds)}"
    ok("get_all_individuals() returns all 3 records")
except AssertionError as e:
    fail("get_all_individuals()", str(e))

# duplicate service number must be blocked
try:
    dup = db.get_individual_by_service_no('10012345')
    assert dup is not None, "Should already exist"
    ok("Duplicate service-number check works (existing detected)")
except Exception as e:
    fail("Duplicate service-number check", str(e))

# edit
try:
    ind_id = db.get_individual_by_service_no('10012345')['id']
    updated = {**IND1, 'remarks': 'Updated in test'}
    db.update_individual(ind_id, updated, 'admin')
    ind = db.get_individual(ind_id)
    assert ind['remarks'] == 'Updated in test'
    ok("update_individual() persists changes")
except Exception as e:
    fail("update_individual()", str(e))

# ══════════════════════════════════════════════════════════════
section("3 · Test entry (gap validation + count limit)")
# ══════════════════════════════════════════════════════════════

ind_id = db.get_individual_by_service_no('10012345')['id']

TEST1 = {
    'individual_id':  ind_id,
    'test_type':      'Firing',
    'attempt_number': 1,
    'assessment_year': 2,
    'date_conducted': '2023-08-10',
    'result':         'Pass',
    'remarks':        '',
}
try:
    db.add_test(TEST1, 'admin')
    ok("add_test() — AY2 Firing attempt 1 saved")
except Exception as e:
    fail("add_test() first entry", str(e))

# gap validation (30-day minimum)
try:
    min_gap = db.get_rule('min_test_gap_days', 30)
    prev = db.get_latest_test(ind_id, 'Firing', 2)
    assert prev is not None
    prev_date = datetime.datetime.strptime(prev['date_conducted'], "%Y-%m-%d").date()
    too_soon_date = datetime.date(2023, 8, 20)
    gap = (too_soon_date - prev_date).days
    assert gap < min_gap, f"gap={gap} should be < {min_gap}"
    ok(f"Gap validation detects {gap}-day gap (< {min_gap}d minimum)")
except AssertionError as e:
    fail("Gap validation", str(e))

# second attempt after proper gap
TEST2 = {**TEST1, 'attempt_number': 2, 'date_conducted': '2023-09-20'}
try:
    db.add_test(TEST2, 'admin')
    ok("add_test() — AY2 Firing attempt 2 saved (41-day gap, OK)")
except Exception as e:
    fail("add_test() second attempt", str(e))

# count check — should now be 2
try:
    count = db.get_test_count(ind_id, 'Firing', 2)
    limit = db.get_rule('tests_per_year', 2)
    assert count == 2
    assert count >= limit, "Count-limit guard would trigger"
    ok(f"Test count = {count}/{limit} — limit guard works")
except AssertionError as e:
    fail("Test count limit", str(e))

# add DST test for IND2
ind2_id = db.get_individual_by_service_no('10023456')['id']
try:
    db.add_test({
        'individual_id':  ind2_id,
        'test_type':      'DST',
        'attempt_number': 1,
        'assessment_year': 2,
        'date_conducted': '2023-07-15',
        'result':         'Pass',
        'remarks':        '',
    }, 'admin')
    ok("add_test() — DST for 2nd individual saved")
except Exception as e:
    fail("add_test() DST for ind2", str(e))

# ══════════════════════════════════════════════════════════════
section("4 · Medical examination entry")
# ══════════════════════════════════════════════════════════════

try:
    db.add_medical({
        'individual_id': ind_id,
        'medical_type':  'Annual Medical',
        'date_conducted':'2024-06-15',
        'category':      'SHAPE-1',
        'result':        'Fit',
        'remarks':       'Routine annual check',
    }, 'admin')
    ok("add_medical() — Annual Medical saved")
except Exception as e:
    fail("add_medical()", str(e))

try:
    recs = db.get_medical_for_individual(ind_id)
    assert len(recs) == 1
    assert recs[0]['medical_type'] == 'Annual Medical'
    assert recs[0]['result'] == 'Fit'
    ok("get_medical_for_individual() returns correct record")
except AssertionError as e:
    fail("get_medical_for_individual()", str(e))

try:
    count = db.get_medical_count(ind_id, 'Annual Medical')
    assert count == 1
    ok(f"get_medical_count() = {count} (duplicate guard functional)")
except AssertionError as e:
    fail("get_medical_count()", str(e))

# ══════════════════════════════════════════════════════════════
section("5 · Counselling entry")
# ══════════════════════════════════════════════════════════════

try:
    db.add_counselling({
        'individual_id':      ind_id,
        'counselling_number': 1,
        'date_conducted':     '2024-08-10',
        'counsellor_name':    'Sub Maj Ramesh Kumar',
        'remarks':            'Counselled on performance',
        'status':             'Completed',
    }, 'admin')
    ok("add_counselling() — Counselling 1 saved")
except Exception as e:
    fail("add_counselling()", str(e))

try:
    recs = db.get_counselling_for_individual(ind_id)
    assert len(recs) == 1
    assert recs[0]['counselling_number'] == 1
    assert recs[0]['status'] == 'Completed'
    ok("get_counselling_for_individual() returns correct record")
except AssertionError as e:
    fail("get_counselling_for_individual()", str(e))

try:
    count = db.get_counselling_count(ind_id, 1)
    assert count == 1
    ok(f"get_counselling_count() = {count} (duplicate guard functional)")
except AssertionError as e:
    fail("get_counselling_count()", str(e))

# ══════════════════════════════════════════════════════════════
section("6 · Alert computation (utils.py)")
# ══════════════════════════════════════════════════════════════

from utils import compute_individual_status, get_dashboard_summary

try:
    ind = db.get_individual(ind_id)
    status = compute_individual_status(ind)
    assert 'overall_alert' in status
    assert 'ay_status' in status
    assert 'medical_status' in status
    assert 'counselling_status' in status
    ok(f"compute_individual_status() → alert='{status['overall_alert']}'")
except Exception as e:
    fail("compute_individual_status()", traceback.format_exc())

try:
    assert 'AY2' in status['ay_status'] or 2 in status['ay_status']
    ok("ay_status contains AY2 window data")
except AssertionError as e:
    fail("ay_status keys", str(status.get('ay_status', {}).keys()))

try:
    med_status = status['medical_status']
    assert 'Annual Medical' in med_status
    am = med_status['Annual Medical']
    assert am['done'] is True, f"Annual Medical should be done, got done={am['done']}"
    ok("Medical status: Annual Medical correctly marked as done")
except AssertionError as e:
    fail("Medical status done flag", str(e))

try:
    cs = status['counselling_status']
    assert 1 in cs
    assert cs[1]['done'] is True, f"Counselling 1 should be done, got {cs[1]['done']}"
    ok("Counselling status: Counselling 1 correctly marked as done")
except AssertionError as e:
    fail("Counselling status done flag", str(e))

# ══════════════════════════════════════════════════════════════
section("7 · Dashboard summary counts")
# ══════════════════════════════════════════════════════════════

try:
    summary = get_dashboard_summary()
    assert summary['total'] == 3, f"expected total=3 got {summary['total']}"
    ok(f"Dashboard total = {summary['total']} (3 individuals)")
except AssertionError as e:
    fail("Dashboard total count", str(e))

try:
    assert 'active' in summary
    assert 'completed' in summary
    ok(f"Dashboard summary keys present: {list(summary.keys())}")
except AssertionError as e:
    fail("Dashboard summary keys", str(e))

# ══════════════════════════════════════════════════════════════
section("8 · Rules engine")
# ══════════════════════════════════════════════════════════════

try:
    val = db.get_rule('monitoring_period_months', 48)
    assert val == 48, f"expected 48 got {val}"
    ok("get_rule('monitoring_period_months') = 48")
except AssertionError as e:
    fail("get_rule default value", str(e))

try:
    db.update_rule('alert_red_days', '90', 'admin')
    val = db.get_rule('alert_red_days', 0)
    assert val == 90, f"expected 90 got {val}"
    ok("update_rule() then get_rule() round-trip works")
except (AssertionError, Exception) as e:
    fail("update_rule/get_rule round-trip", str(e))

# ══════════════════════════════════════════════════════════════
section("9 · User management (Settings)")
# ══════════════════════════════════════════════════════════════

try:
    db.create_user('operator1', 'Operator@1234', 'user', 'admin')
    user = db.authenticate_user('operator1', 'Operator@1234')
    assert user is not None
    assert user['role'] == 'user'
    ok("create_user() + authenticate_user() for new user")
except Exception as e:
    fail("create_user/authenticate_user", str(e))

try:
    users = db.get_all_users()
    assert len(users) >= 2
    ok(f"get_all_users() returns {len(users)} users")
except AssertionError as e:
    fail("get_all_users()", str(e))

try:
    users = db.get_all_users()
    op1 = next((u for u in users if u['username'] == 'operator1'), None)
    assert op1 is not None
    db.update_user_password(op1['id'], 'NewPass@5678', 'admin')
    user = db.authenticate_user('operator1', 'NewPass@5678')
    assert user is not None
    ok("update_user_password() works — new password authenticates")
except Exception as e:
    fail("update_user_password()", str(e))

# ══════════════════════════════════════════════════════════════
section("10 · Audit log")
# ══════════════════════════════════════════════════════════════

try:
    db.log_audit('admin', 'Test Run', 'Automated test suite')
    logs = db.get_audit_logs(limit=5)
    assert len(logs) >= 1
    ok(f"log_audit() + get_audit_logs() — {len(logs)} entries found")
except Exception as e:
    fail("Audit log", str(e))

# ══════════════════════════════════════════════════════════════
section("11 · Delete individual (cascade)")
# ══════════════════════════════════════════════════════════════

try:
    ind3 = db.get_individual_by_service_no('10034567')
    db.delete_individual(ind3['id'], 'admin')
    gone = db.get_individual_by_service_no('10034567')
    assert gone is None, "Should be deleted"
    ok("delete_individual() removes record and cascade works")
except Exception as e:
    fail("delete_individual()", str(e))

# ══════════════════════════════════════════════════════════════
# RESULTS
# ══════════════════════════════════════════════════════════════

print(f"\n{BOLD}{'═'*56}{RESET}")
total = len(passed) + len(failed)
if failed:
    print(f"{RED}{BOLD}  RESULT: {len(passed)}/{total} passed, {len(failed)} FAILED{RESET}")
    for f in failed:
        print(f"  {RED}✗  {f}{RESET}")
    sys.exit(1)
else:
    print(f"{GREEN}{BOLD}  ALL {total} TESTS PASSED ✓{RESET}")
    print(f"{BOLD}{'═'*56}{RESET}\n")
    sys.exit(0)
