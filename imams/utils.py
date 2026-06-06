import datetime
from dateutil.relativedelta import relativedelta
from database import get_rule, get_all_individuals, get_tests_for_individual, \
    get_medical_for_individual, get_counselling_for_individual, get_test_count, \
    get_medical_count, get_counselling_count


TEST_TYPES = ["Firing", "DST", "BPET", "PPT"]
ASSESSMENT_YEARS = [2, 3, 4]


def months_elapsed(enrollment_date_str: str) -> float:
    try:
        enroll = datetime.datetime.strptime(enrollment_date_str, "%Y-%m-%d").date()
        today = datetime.date.today()
        delta = relativedelta(today, enroll)
        return delta.years * 12 + delta.months + delta.days / 30.0
    except Exception:
        return 0


def get_assessment_year_windows():
    return {
        2: (get_rule('ay2_start_month', 7), get_rule('ay2_end_month', 18)),
        3: (get_rule('ay3_start_month', 19), get_rule('ay3_end_month', 30)),
        4: (get_rule('ay4_start_month', 31), get_rule('ay4_end_month', 42)),
    }


def get_window_end_date(enrollment_date_str: str, end_month: int) -> datetime.date:
    try:
        enroll = datetime.datetime.strptime(enrollment_date_str, "%Y-%m-%d").date()
        return enroll + relativedelta(months=end_month)
    except Exception:
        return datetime.date.today()


def get_window_start_date(enrollment_date_str: str, start_month: int) -> datetime.date:
    try:
        enroll = datetime.datetime.strptime(enrollment_date_str, "%Y-%m-%d").date()
        return enroll + relativedelta(months=start_month)
    except Exception:
        return datetime.date.today()


def days_until(target_date: datetime.date) -> int:
    return (target_date - datetime.date.today()).days


def get_alert_color(days_remaining: int, overdue: bool) -> str:
    if overdue:
        return "overdue"
    if days_remaining <= get_rule('alert_red_days', 90):
        return "red"
    if days_remaining <= get_rule('alert_orange_days', 120):
        return "orange"
    if days_remaining <= get_rule('alert_yellow_days', 150):
        return "yellow"
    return "green"


def compute_individual_status(individual: dict) -> dict:
    """
    Returns a rich status dict for one individual covering:
    - monitoring_complete, monitoring_end_date
    - per-AY per-test completion
    - medical status
    - counselling status
    - overall alert level
    """
    enrollment_date = individual.get('enrollment_date', '')
    ind_id = individual['id']
    today = datetime.date.today()

    monitoring_months = get_rule('monitoring_period_months', 48)
    end_date = get_window_end_date(enrollment_date, monitoring_months)
    monitoring_complete = today >= end_date

    ay_windows = get_assessment_year_windows()
    tests_per_year = get_rule('tests_per_year', 2)

    ay_status = {}
    for ay, (start_m, end_m) in ay_windows.items():
        start_date = get_window_start_date(enrollment_date, start_m)
        end_date_ay = get_window_end_date(enrollment_date, end_m)
        overdue = today > end_date_ay
        days_left = days_until(end_date_ay)
        test_status = {}
        for tt in TEST_TYPES:
            count = get_test_count(ind_id, tt, ay)
            done = count >= tests_per_year
            test_status[tt] = {
                'count': count,
                'required': tests_per_year,
                'done': done,
                'overdue': overdue and not done,
                'days_left': days_left,
                'alert': get_alert_color(days_left, overdue and not done) if not done else 'green',
            }
        ay_status[ay] = {
            'start_date': start_date,
            'end_date': end_date_ay,
            'overdue': overdue,
            'days_left': days_left,
            'tests': test_status,
        }

    # Medical
    annual_med_start = get_rule('annual_medical_start_month', 25)
    annual_med_end = get_rule('annual_medical_end_month', 30)
    exit_med_start = get_rule('exit_medical_start_month', 42)
    exit_med_end = get_rule('exit_medical_end_month', 45)

    def med_status(med_type, start_m, end_m):
        s_date = get_window_start_date(enrollment_date, start_m)
        e_date = get_window_end_date(enrollment_date, end_m)
        count = get_medical_count(ind_id, med_type)
        done = count >= 1
        overdue = today > e_date and not done
        d_left = days_until(e_date)
        return {
            'done': done,
            'count': count,
            'overdue': overdue,
            'days_left': d_left,
            'start_date': s_date,
            'end_date': e_date,
            'alert': get_alert_color(d_left, overdue) if not done else 'green',
        }

    medical_status = {
        'Annual Medical': med_status('Annual Medical', annual_med_start, annual_med_end),
        'Exit Medical': med_status('Exit Medical', exit_med_start, exit_med_end),
    }

    # Counselling
    c1_start = get_rule('counselling1_start_month', 19)
    c1_end = get_rule('counselling1_end_month', 24)
    c2_start = get_rule('counselling2_start_month', 31)
    c2_end = get_rule('counselling2_end_month', 36)

    def counsel_status(num, start_m, end_m):
        s_date = get_window_start_date(enrollment_date, start_m)
        e_date = get_window_end_date(enrollment_date, end_m)
        count = get_counselling_count(ind_id, num)
        done = count >= 1
        overdue = today > e_date and not done
        d_left = days_until(e_date)
        return {
            'done': done,
            'count': count,
            'overdue': overdue,
            'days_left': d_left,
            'start_date': s_date,
            'end_date': e_date,
            'alert': get_alert_color(d_left, overdue) if not done else 'green',
        }

    counselling_status = {
        1: counsel_status(1, c1_start, c1_end),
        2: counsel_status(2, c2_start, c2_end),
    }

    # Overall alert
    alert_priority = {'overdue': 0, 'red': 1, 'orange': 2, 'yellow': 3, 'green': 4}
    all_alerts = []
    for ay, ay_data in ay_status.items():
        for tt, ts in ay_data['tests'].items():
            all_alerts.append(ts['alert'])
    for ms in medical_status.values():
        all_alerts.append(ms['alert'])
    for cs in counselling_status.values():
        all_alerts.append(cs['alert'])

    if monitoring_complete:
        overall = 'green'
    elif all_alerts:
        overall = min(all_alerts, key=lambda x: alert_priority.get(x, 99))
    else:
        overall = 'green'

    monitoring_end = get_window_end_date(enrollment_date, monitoring_months)

    return {
        'monitoring_complete': monitoring_complete,
        'monitoring_end_date': monitoring_end,
        'ay_status': ay_status,
        'medical_status': medical_status,
        'counselling_status': counselling_status,
        'overall_alert': overall,
    }


def get_dashboard_summary():
    individuals = get_all_individuals()
    total = len(individuals)
    active = 0
    completed = 0
    overdue_count = 0
    red_count = 0
    orange_count = 0
    yellow_count = 0

    for ind in individuals:
        status = compute_individual_status(ind)
        if status['monitoring_complete']:
            completed += 1
        else:
            active += 1
            alert = status['overall_alert']
            if alert == 'overdue':
                overdue_count += 1
            elif alert == 'red':
                red_count += 1
            elif alert == 'orange':
                orange_count += 1
            elif alert == 'yellow':
                yellow_count += 1

    return {
        'total': total,
        'active': active,
        'completed': completed,
        'overdue': overdue_count,
        'red': red_count,
        'orange': orange_count,
        'yellow': yellow_count,
    }


def search_individuals(query: str):
    """Parse command bar query and return matching individuals with status."""
    individuals = get_all_individuals()
    query_lower = query.strip().lower()
    results = []

    def status_match(ind, target_alert):
        s = compute_individual_status(ind)
        return s['overall_alert'] == target_alert

    def test_pending(ind, test_type):
        s = compute_individual_status(ind)
        for ay, ay_data in s['ay_status'].items():
            ts = ay_data['tests'].get(test_type)
            if ts and not ts['done']:
                return True
        return False

    def medical_pending(ind, med_type=None):
        s = compute_individual_status(ind)
        for mt, ms in s['medical_status'].items():
            if (med_type is None or mt.lower() == med_type.lower()) and not ms['done']:
                return True
        return False

    def counselling_pending(ind):
        s = compute_individual_status(ind)
        for cs in s['counselling_status'].values():
            if not cs['done']:
                return True
        return False

    def due_in_days(ind, days):
        s = compute_individual_status(ind)
        for ay, ay_data in s['ay_status'].items():
            for tt, ts in ay_data['tests'].items():
                if not ts['done'] and 0 < ts['days_left'] <= days:
                    return True
        for ms in s['medical_status'].values():
            if not ms['done'] and 0 < ms['days_left'] <= days:
                return True
        for cs in s['counselling_status'].values():
            if not cs['done'] and 0 < cs['days_left'] <= days:
                return True
        return False

    for ind in individuals:
        matched = False
        s = compute_individual_status(ind)

        if query_lower in ('show overdue', 'overdue'):
            matched = s['overall_alert'] == 'overdue'
        elif query_lower in ('show red alerts', 'red', 'show red'):
            matched = s['overall_alert'] == 'red'
        elif query_lower in ('show orange alerts', 'orange', 'show orange'):
            matched = s['overall_alert'] == 'orange'
        elif query_lower in ('show yellow alerts', 'yellow', 'show yellow'):
            matched = s['overall_alert'] == 'yellow'
        elif query_lower in ('show completed', 'completed'):
            matched = s['monitoring_complete']
        elif 'firing pending' in query_lower:
            matched = test_pending(ind, 'Firing')
        elif 'dst pending' in query_lower:
            matched = test_pending(ind, 'DST')
        elif 'bpet pending' in query_lower:
            matched = test_pending(ind, 'BPET')
        elif 'ppt pending' in query_lower:
            matched = test_pending(ind, 'PPT')
        elif 'medical pending' in query_lower or 'annual medical due' in query_lower:
            matched = medical_pending(ind, 'Annual Medical')
        elif 'exit medical due' in query_lower:
            matched = medical_pending(ind, 'Exit Medical')
        elif 'counselling pending' in query_lower:
            matched = counselling_pending(ind)
        elif query_lower.startswith('show batch '):
            batch = query_lower.replace('show batch ', '').strip()
            matched = ind.get('batch', '').lower() == batch
        elif query_lower.startswith('show unit '):
            unit = query_lower.replace('show unit ', '').strip()
            matched = unit in ind.get('unit', '').lower()
        elif query_lower.startswith('show service no '):
            svc = query_lower.replace('show service no ', '').strip()
            matched = svc in ind.get('service_number', '').lower()
        elif query_lower.startswith('show name '):
            name = query_lower.replace('show name ', '').strip()
            matched = name in ind.get('name', '').lower()
        elif 'due in next 90 days' in query_lower:
            matched = due_in_days(ind, 90)
        elif 'due in next 120 days' in query_lower:
            matched = due_in_days(ind, 120)
        elif 'due in next 150 days' in query_lower:
            matched = due_in_days(ind, 150)
        elif 'all individuals' in query_lower or query_lower == '':
            matched = True
        else:
            # Fuzzy match on name / service number
            matched = (query_lower in ind.get('name', '').lower() or
                       query_lower in ind.get('service_number', '').lower() or
                       query_lower in ind.get('unit', '').lower() or
                       query_lower in ind.get('batch', '').lower())

        if matched:
            results.append({**ind, 'status': s})

    return results


ALERT_HEX = {
    'green': '#27AE60',
    'yellow': '#F1C40F',
    'orange': '#E67E22',
    'red': '#E74C3C',
    'overdue': '#8E44AD',
}
