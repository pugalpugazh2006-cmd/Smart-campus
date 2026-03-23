from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from tinydb import Query, where
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
from sqlalchemy import text
from config import Config
from functools import wraps
import datetime
import qrcode
import io
import base64
import uuid
import math
import hashlib
import os
import tempfile
import time

# Proximity Verification Helper
def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    if None in [lat1, lon1, lat2, lon2]:
        return float('inf')
        
    try:
        # convert decimal degrees to radians 
        lat1, lon1, lat2, lon2 = map(math.radians, [float(lat1), float(lon1), float(lat2), float(lon2)])

        # haversine formula 
        dlon = lon2 - lon1 
        dlat = lat2 - lat1 
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a)) 
        r = 6371 # Radius of earth in kilometers
        return c * r * 1000 # Return in meters
    except (ValueError, TypeError):
        return float('inf')

def generate_timed_token(session_id, secret, window_offset=0):
    """Generates a token based on session secret and 120s windows"""
    window = int(time.time() / 120) + window_offset
    payload = f"{session_id}-{secret}-{window}"
    return hashlib.sha256(payload.encode()).hexdigest()[:16]

app = Flask(__name__)
app.config.from_object(Config)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# PWA Routes
@app.route('/manifest.json')
def serve_manifest():
    return send_file('static/manifest.json')

@app.route('/sw.js')
def serve_sw():
    return send_file('static/sw.js')

@app.route('/offline')
def offline():
    return render_template('offline.html')

# TinyDB to SQLAlchemy Mock Initialization
from mock_db import MockDB
from models import db as sql_db

sql_db.init_app(app)

def initialize_database():
    with app.app_context():
        sql_db.create_all()
        ensure_default_admin()

db = MockDB()
User = Query()

def append_notification_log(lines):
    log_path = os.path.join(tempfile.gettempdir(), 'smart_campus_notifications.log')
    with open(log_path, 'a', encoding='utf-8') as log_file:
        log_file.write('\n'.join(lines) + '\n')
    return log_path

@app.route('/healthz')
def healthz():
    try:
        sql_db.session.execute(text('SELECT 1'))
        return {'status': 'ok', 'database': 'connected'}, 200
    except Exception as exc:
        return {'status': 'error', 'database': 'unavailable', 'detail': str(exc)}, 503

def create_user_account(username, email, password, role, full_name, roll_number=None, department=None):
    user_id = db.table('users').insert({
        'username': username,
        'email': email,
        'password_hash': generate_password_hash(password),
        'role': role
    })

    if role == 'student':
        db.table('student_profiles').insert({
            'user_id': user_id,
            'full_name': full_name,
            'roll_number': roll_number or f"STU{user_id}",
            'department': department or 'General',
            'semester': 1
        })
    elif role == 'faculty':
        db.table('faculty_profiles').insert({
            'user_id': user_id,
            'full_name': full_name,
            'department': department or 'General'
        })
    elif role == 'admin':
        db.table('admin_profiles').insert({
            'user_id': user_id,
            'full_name': full_name,
            'title': 'System Admin'
        })

    return user_id

def ensure_default_admin():
    admin_user = db.table('users').get(where('role') == 'admin')
    if admin_user:
        return admin_user.doc_id

    return create_user_account(
        username='admin',
        email='admin@smartcampus.com',
        password='admin123',
        role='admin',
        full_name='Administrator'
    )

initialize_database()

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Role required decorator
def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session.get('role') != role:
                flash('Access denied!', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = db.table('users').get(User.username == username)

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user.doc_id
            session['username'] = user['username']
            session['role'] = user['role']
            flash('Successfully logged in!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        email = (request.form.get('email') or '').strip().lower()
        password = request.form.get('password') or ''
        confirm_password = request.form.get('confirm_password') or ''
        full_name = (request.form.get('full_name') or '').strip()
        roll_number = (request.form.get('roll_number') or '').strip()
        department = (request.form.get('department') or '').strip()

        if not all([username, email, password, confirm_password, full_name]):
            flash('All required fields must be filled in.', 'danger')
            return render_template('signup.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('signup.html')

        if len(password) < 8:
            flash('Password must be at least 8 characters long.', 'danger')
            return render_template('signup.html')

        if db.table('users').get(User.username == username) or db.table('users').get(where('email') == email):
            flash('Username or Email already exists!', 'danger')
            return render_template('signup.html')

        if roll_number and db.table('student_profiles').get(where('roll_number') == roll_number):
            flash('Roll number already exists!', 'danger')
            return render_template('signup.html')

        user_id = create_user_account(
            username=username,
            email=email,
            password=password,
            role='student',
            full_name=full_name,
            roll_number=roll_number or None,
            department=department or None
        )

        session['user_id'] = user_id
        session['username'] = username
        session['role'] = 'student'
        flash('Account created successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Successfully logged out!', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    role = session['role']

    stats = {}
    if role == 'student':
        # Attendance %
        attendance_records = db.table('attendance').search(where('student_id') == user_id)
        if attendance_records:
            present_count = sum(1 for r in attendance_records if r['status'] == 'Present')
            stats['attendance'] = (present_count * 100) / len(attendance_records)
        else:
            stats['attendance'] = 0
        
        # Fee Status
        fee = db.table('fees').get(where('student_id') == user_id)
        stats['fee_status'] = fee['status'] if fee else 'N/A'
        
        # Marks (Internal)
        stats['performance'] = db.table('performance').search(where('student_id') == user_id)
        
        # Borrowed Books
        stats['borrowed_count'] = len(db.table('library_records').search((where('student_id') == user_id) & (where('status') == 'Borrowed')))

    elif role == 'faculty':
        stats['student_count'] = len(db.table('student_profiles'))
        stats['active_qr_sessions'] = len(db.table('qr_sessions').search(where('created_by') == user_id))
        
    elif role == 'admin':
        roles = {}
        for user in db.table('users'):
            r = user['role']
            roles[r] = roles.get(r, 0) + 1
        stats['user_stats'] = [{'role': r, 'count': c} for r, c in roles.items()]
        stats['total_books'] = len(db.table('library'))

    return render_template('dashboard.html', stats=stats)

# Attendance Routes
@app.route('/attendance')
@login_required
def attendance():
    user_id = session['user_id']
    role = session['role']
    
    if role == 'student':
        records = db.table('attendance').search(where('student_id') == user_id)
        records.sort(key=lambda x: x['date'], reverse=True)
        for r in records:
            faculty = db.table('users').get(doc_id=int(r['marked_by']))
            r['faculty_name'] = faculty['username'] if faculty else 'Unknown'
        return render_template('attendance.html', records=records)
    
    elif role == 'faculty':
        students = db.table('student_profiles').all()
        # Fetch records marked by this faculty
        history = db.table('attendance').search(where('marked_by') == user_id)
        history.sort(key=lambda x: x['date'], reverse=True)
        
        for h in history:
            student = db.table('student_profiles').get(where('user_id') == h['student_id'])
            h['student_name'] = student['full_name'] if student else 'Unknown'
            h['roll_number'] = student['roll_number'] if student else 'N/A'
            
        return render_template('attendance.html', students=students, history=history)
    
    return redirect(url_for('dashboard'))

@app.route('/mark-attendance', methods=['POST'])
@login_required
@role_required('faculty')
def mark_attendance():
    student_ids = request.form.getlist('attendance')
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    
    for sid in student_ids:
        db.table('attendance').insert({
            'student_id': int(sid),
            'date': today,
            'status': 'Present',
            'marked_by': session['user_id']
        })
    
    flash('Attendance marked successfully!', 'success')
    return redirect(url_for('attendance'))

# QR Attendance Routes
@app.route('/qr-attendance')
@login_required
@role_required('faculty')
def qr_attendance():
    sessions = db.table('qr_sessions').search(where('created_by') == session['user_id'])
    for s in sessions:
        s['id'] = s.doc_id
    return render_template('qr_attendance.html', sessions=sessions)

@app.route('/qr-scan')
@login_required
@role_required('student')
def qr_student_portal():
    return render_template('student_qr.html')

@app.route('/generate-qr', methods=['POST'])
@login_required
@role_required('faculty')
def generate_qr():
    subject = request.form.get('subject')
    session_secret = str(uuid.uuid4())
    
    session_id = db.table('qr_sessions').insert({
        'subject': subject,
        'secret': session_secret,
        'created_by': session['user_id'],
        'created_at': datetime.datetime.now().isoformat(),
        'active': True,
        'latitude': request.form.get('latitude'),
        'longitude': request.form.get('longitude')
    })
    
    token = generate_timed_token(session_id, session_secret)
    db.table('qr_sessions').update({'current_token': token}, doc_ids=[session_id])
    
    # Generate QR Code
    qr_url = url_for('scan_qr', token=token, _external=True)
    img = qrcode.make(qr_url)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    qr_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    
    return render_template('qr_attendance.html', qr_code=qr_base64, subject=subject, token=token, session_id=session_id)

@app.route('/api/qr-refresh/<int:session_id>')
@login_required
@role_required('faculty')
def api_qr_refresh(session_id):
    qr_session = db.table('qr_sessions').get(doc_id=session_id)
    if not qr_session or qr_session['created_by'] != session['user_id']:
        return {"error": "Unauthorized"}, 401
    
    token = generate_timed_token(session_id, qr_session['secret'])
    qr_url = url_for('scan_qr', token=token, _external=True)
    img = qrcode.make(qr_url)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    qr_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    
    return {
        "qr_code": qr_base64,
        "token": token,
        "expires_in": 120 - (int(time.time()) % 120)
    }

@app.route('/scan-qr/<token>')
@login_required
@role_required('student')
def scan_qr(token):
    # Find the active session this token belongs to
    all_active = db.table('qr_sessions').search(where('active') == True)
    qr_session = None
    
    for s in all_active:
        t0 = generate_timed_token(s.doc_id, s['secret'], 0)
        t1 = generate_timed_token(s.doc_id, s['secret'], -1)
        if token in [t0, t1]:
            qr_session = s
            break

    if not qr_session:
        flash('Invalid or expired QR code', 'danger')
        return redirect(url_for('dashboard'))
    
    # Check if already marked
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    exists = db.table('attendance').get(
        (where('student_id') == session['user_id']) & 
        (where('date') == today) & 
        (where('marked_by') == qr_session['created_by'])
    )
    
    if exists:
        flash('Attendance already marked for this session today!', 'info')
        return redirect(url_for('attendance'))

    return render_template('verify_location.html', token=token, subject=qr_session['subject'])

@app.route('/verify-attendance', methods=['POST'])
@login_required
@role_required('student')
def verify_attendance():
    token = request.form.get('token')
    lat = request.form.get('latitude')
    lng = request.form.get('longitude')
    
    # Find session
    all_active = db.table('qr_sessions').search(where('active') == True)
    qr_session = None
    for s in all_active:
        t0 = generate_timed_token(s.doc_id, s['secret'], 0)
        t1 = generate_timed_token(s.doc_id, s['secret'], -1)
        if token in [t0, t1]:
            qr_session = s
            break

    if not qr_session:
        return {"status": "error", "message": "Invalid or expired session"}, 400
        
    print(f"[DEBUG] Location Verification - Session ID: {qr_session.doc_id}", flush=True)
    print(f"[DEBUG] Session Coords: ({qr_session.get('latitude')}, {qr_session.get('longitude')})", flush=True)
    print(f"[DEBUG] Student Coords: ({lat}, {lng})", flush=True)
    
    distance = calculate_distance(
        qr_session.get('latitude'), qr_session.get('longitude'),
        lat, lng
    )
    print(f"[DEBUG] Calculated Distance: {distance}m", flush=True)
    
    # Students must be within 100 meters of the faculty location.
    if distance > 100:
        msg = f"Out of range! You are {round(distance)}m away from the classroom zone."
        print(f"[DEBUG] Verification Failed: {msg}", flush=True)
        return {"status": "error", "message": msg}, 403
        
    # Mark attendance
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    faculty = db.table('users').get(doc_id=qr_session['created_by'])
    
    db.table('attendance').insert({
        'student_id': session['user_id'],
        'date': today,
        'status': 'Present',
        'marked_by': qr_session['created_by'],
        'faculty_name': faculty['username'] if faculty else 'Faculty',
        'verified_at': datetime.datetime.now().isoformat(),
        'distance_m': round(distance, 2)
    })
    
    return {"status": "success", "message": "Attendance marked successfully!"}

# Performance Analyzer Routes
@app.route('/performance-analyzer')
@login_required
def performance_analyzer():
    user_id = session['user_id']
    role = session['role']
    
    if role == 'student':
        performance = db.table('performance').search(where('student_id') == user_id)
        
        # Calculate CGPA
        total_grade_points = 0
        total_credits = 0
        for p in performance:
            gp = p.get('grade_point', 0)
            credits = p.get('credits', 1)
            total_grade_points += (gp * credits)
            total_credits += credits
            
        cgpa = round(total_grade_points / total_credits, 2) if total_credits > 0 else 0
        
        return render_template('performance_analyzer.html', performance=performance, cgpa=cgpa)
    
    elif role in ['admin', 'faculty']:
        # Show breakdown of all students for staff
        all_performance = db.table('performance').all()
        student_stats = {} # {student_id: {total_gp, total_credits}}
        
        for p in all_performance:
            sid = p['student_id']
            if sid not in student_stats:
                student_stats[sid] = {'gp': 0, 'credits': 0, 'name': 'Unknown'}
                profile = db.table('student_profiles').get(where('user_id') == sid)
                if profile: student_stats[sid]['name'] = profile['full_name']
                
            student_stats[sid]['gp'] += (p.get('grade_point', 0) * p.get('credits', 1))
            student_stats[sid]['credits'] += p.get('credits', 1)
            
        rankings = []
        for sid, data in student_stats.items():
            avg_cgpa = round(data['gp'] / data['credits'], 2) if data['credits'] > 0 else 0
            rankings.append({'name': data['name'], 'cgpa': avg_cgpa})
            
        rankings.sort(key=lambda x: x['cgpa'], reverse=True)
        return render_template('performance_analyzer.html', rankings=rankings)
    
    return redirect(url_for('dashboard'))

# Transport Routes
@app.route('/transport')
@login_required
def transport():
    user_id = session['user_id']
    role = session['role']
    
    buses = db.table('transport').all()
    my_bus = None
    
    if role == 'student':
        assignment = db.table('student_transport').get(where('student_id') == user_id)
        if assignment:
            my_bus = db.table('transport').get(doc_id=assignment['transport_id'])
            
    return render_template('transport.html', buses=buses, my_bus=my_bus)

@app.route('/add-transport', methods=['POST'])
@login_required
def add_transport():
    if session['role'] != 'admin':
        flash('Admin access required!', 'danger')
        return redirect(url_for('transport'))
        
    db.table('transport').insert({
        'bus_no': request.form.get('bus_no'),
        'driver': request.form.get('driver'),
        'contact': request.form.get('contact'),
        'route': request.form.get('route'),
        'timing': request.form.get('timing')
    })
    flash('Transport route added!', 'success')
    return redirect(url_for('transport'))

@app.route('/assign-transport', methods=['POST'])
@login_required
def assign_transport():
    if session['role'] != 'admin':
        flash('Admin access required!', 'danger')
        return redirect(url_for('transport'))
        
    student_id = int(request.form.get('student_id'))
    transport_id = int(request.form.get('transport_id'))
    
    # Update or Insert
    db.table('student_transport').upsert(
        {'student_id': student_id, 'transport_id': transport_id, 'assigned_at': datetime.datetime.now().isoformat()},
        (where('student_id') == student_id)
    )
    flash('Transport assigned to student!', 'success')
    return redirect(url_for('transport'))

# Library Routes
@app.route('/library')
@login_required
def library():
    books = db.table('library').all()
    for b in books:
        b['id'] = b.doc_id
        # Check availability
        b['is_available'] = b.get('copies', 1) > len(db.table('library_records').search((where('book_id') == b.doc_id) & (where('status') == 'Borrowed')))
    
    my_books = []
    if session['role'] == 'student':
        my_books = db.table('library_records').search((where('student_id') == session['user_id']) & (where('status') == 'Borrowed'))
        for mb in my_books:
            mb['id'] = mb.doc_id
            book = db.table('library').get(doc_id=mb['book_id'])
            mb['title'] = book['title'] if book else 'Unknown'
            
    return render_template('library.html', books=books, my_books=my_books)

@app.route('/add-book', methods=['POST'])
@login_required
def add_book():
    if session['role'] not in ['admin', 'faculty']:
        flash('Access denied!', 'danger')
        return redirect(url_for('library'))
    
    title = request.form.get('title')
    author = request.form.get('author')
    isbn = request.form.get('isbn')
    category = request.form.get('category')
    copies = int(request.form.get('copies', 1))
    
    db.table('library').insert({
        'title': title,
        'author': author,
        'isbn': isbn,
        'category': category,
        'copies': copies
    })
    flash('Book added successfully!', 'success')
    return redirect(url_for('library'))

@app.route('/borrow-book/<int:book_id>', methods=['POST'])
@login_required
@role_required('student')
def borrow_book(book_id):
    book = db.table('library').get(doc_id=book_id)
    if not book:
        flash('Book not found!', 'danger')
        return redirect(url_for('library'))
    
    # Check availability
    borrowed_count = len(db.table('library_records').search((where('book_id') == book_id) & (where('status') == 'Borrowed')))
    if borrowed_count >= book.get('copies', 1):
        flash('No copies available!', 'warning')
        return redirect(url_for('library'))
    
    # Check if already borrowed by this student
    exists = db.table('library_records').get((where('student_id') == session['user_id']) & (where('book_id') == book_id) & (where('status') == 'Borrowed'))
    if exists:
        flash('You already have this book!', 'info')
        return redirect(url_for('library'))
    
    db.table('library_records').insert({
        'student_id': session['user_id'],
        'book_id': book_id,
        'borrow_date': datetime.datetime.now().isoformat(),
        'status': 'Borrowed'
    })
    flash(f'Borrowed "{book["title"]}" successfully!', 'success')
    return redirect(url_for('library'))

@app.route('/return-book/<int:record_id>', methods=['POST'])
@login_required
def return_book(record_id):
    record = db.table('library_records').get(doc_id=record_id)
    if not record or record['student_id'] != session['user_id']:
        flash('Invalid record!', 'danger')
        return redirect(url_for('library'))
    
    db.table('library_records').update({'status': 'Returned', 'return_date': datetime.datetime.now().isoformat()}, doc_ids=[record_id])
    flash('Book returned successfully!', 'success')
    return redirect(url_for('library'))

@app.route('/risk-analysis')
@login_required
def risk_analysis():
    if session['role'] not in ['admin', 'faculty']:
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))
    
    students = db.table('student_profiles').all()
    risk_report = []
    
    for student in students:
        sid = student['user_id']
        risk_factors = []
        is_at_risk = False
        
        # 1. Attendance Check
        attendance_records = db.table('attendance').search(where('student_id') == sid)
        if attendance_records:
            present_count = sum(1 for r in attendance_records if r['status'] == 'Present')
            att_percentage = round((present_count * 100) / len(attendance_records), 2)
            if att_percentage < 75:
                risk_factors.append(f'Low Attendance ({att_percentage}%)')
                is_at_risk = True
        else:
            att_percentage = 0
            risk_factors.append('No Attendance Records')
            is_at_risk = True
            
        # 2. Performance Check
        performance = db.table('performance').search(where('student_id') == sid)
        total_grade_points = 0
        total_credits = 0
        has_failing_grade = False
        
        for p in performance:
            gp = p.get('grade_point', 0)
            credits = p.get('credits', 1)
            total_grade_points += (gp * credits)
            total_credits += credits
            if gp == 0: # Failing grade logic
                has_failing_grade = True
                
        cgpa = round(total_grade_points / total_credits, 2) if total_credits > 0 else 0
        
        if cgpa < 6.0:
            risk_factors.append(f'Low CGPA ({cgpa})')
            is_at_risk = True
        elif has_failing_grade:
            risk_factors.append('Failing Grade in Subjects')
            is_at_risk = True
            
        if is_at_risk:
            # Determine Risk Level
            if (att_percentage < 75 and att_percentage > 0) and (cgpa < 6.0 or has_failing_grade):
                risk_level = 'High'
            else:
                risk_level = 'Moderate'
                
            risk_report.append({
                'id': sid,
                'name': student['full_name'],
                'roll_number': student['roll_number'],
                'risk_level': risk_level,
                'factors': risk_factors,
                'email': student['parent_email']
            })
            
    return render_template('risk_analysis.html', risk_report=risk_report)

@app.route('/notify-risk/<int:student_id>', methods=['POST'])
@login_required
def notify_risk(student_id):
    if session['role'] not in ['admin', 'faculty']:
        return redirect(url_for('dashboard'))
    
    student = db.table('student_profiles').get(where('user_id') == student_id)
    if student:
        message = f"URGENT: Smart Campus Risk Alert for {student['full_name']}. Please contact the department regarding attendance/academic performance."
        append_notification_log([
            f"[{datetime.datetime.now().isoformat()}] RISK ALERT TO: {student['parent_email']}",
            f"MESSAGE: {message}",
            "-" * 50
        ])
        flash(f"Risk alert sent to {student['full_name']}'s parent.", 'warning')
    return redirect(url_for('risk_analysis'))

@app.route('/schedule-meeting/<int:student_id>', methods=['POST'])
@login_required
def schedule_meeting(student_id):
    if session['role'] not in ['admin', 'faculty']:
        return redirect(url_for('dashboard'))
    
    student = db.table('student_profiles').get(where('user_id') == student_id)
    if student:
        append_notification_log([
            f"[{datetime.datetime.now().isoformat()}] MEETING SCHEDULED: {student['full_name']}",
            f"STAFF: {session['username']}",
            "-" * 50
        ])
        flash(f"Meeting request logged for {student['full_name']}.", 'info')
    return redirect(url_for('risk_analysis'))

# Fee Routes
@app.route('/fees')
@login_required
def fees():
    user_id = session['user_id']
    records = db.table('fees').search(where('student_id') == user_id)
    return render_template('fees.html', records=records)

@app.route('/manage-fees')
@login_required
def manage_fees():
    if session['role'] not in ['admin', 'faculty']:
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))
    
    all_fees = db.table('fees').all()
    for f in all_fees:
        f['id'] = f.doc_id
        student = db.table('student_profiles').get(where('user_id') == f['student_id'])
        f['student_name'] = student['full_name'] if student else 'Unknown'
        f['roll_number'] = student['roll_number'] if student else 'N/A'
        f['parent_email'] = student['parent_email'] if student else 'N/A'
    
    students = db.table('student_profiles').all()
    return render_template('manage_fees.html', fees=all_fees, students=students)

@app.route('/add-fee', methods=['POST'])
@login_required
def add_fee():
    if session['role'] not in ['admin', 'faculty']:
        return redirect(url_for('dashboard'))
    
    student_id = int(request.form.get('student_id'))
    amount = float(request.form.get('amount'))
    description = request.form.get('description')
    due_date = request.form.get('due_date')
    
    db.table('fees').insert({
        'student_id': student_id,
        'amount': amount,
        'description': description,
        'status': 'Pending',
        'due_date': due_date,
        'updated_at': datetime.datetime.now().isoformat()
    })
    flash('Fee record added!', 'success')
    return redirect(url_for('manage_fees'))

@app.route('/mark-paid/<int:fee_id>', methods=['POST'])
@login_required
def mark_paid(fee_id):
    if session['role'] not in ['admin', 'faculty']:
        return redirect(url_for('dashboard'))
    
    db.table('fees').update({'status': 'Paid', 'updated_at': datetime.datetime.now().isoformat()}, doc_ids=[fee_id])
    flash('Fee marked as PAID!', 'success')
    return redirect(url_for('manage_fees'))

@app.route('/send-notification/<int:fee_id>', methods=['POST'])
@login_required
def send_notification(fee_id):
    if session['role'] not in ['admin', 'faculty']:
        return redirect(url_for('dashboard'))
    
    fee = db.table('fees').get(doc_id=fee_id)
    student = db.table('student_profiles').get(where('user_id') == fee['student_id']) if fee else None
    
    if fee and student:
        message = f"ALRT: Dear Parent, a fee of ₹{fee['amount']} for {student['full_name']} is currently {fee['status']}. Due date: {fee['due_date']}."
        message = f"ALRT: Dear Parent, a fee of Rs.{fee['amount']} for {student['full_name']} is currently {fee['status']}. Due date: {fee['due_date']}."
        
        # Simulate SMS/Email by logging
        append_notification_log([
            f"[{datetime.datetime.now().isoformat()}] TO: {student['parent_email']} / {student['parent_phone']}",
            f"MESSAGE: {message}",
            "-" * 50
        ])
        
        flash(f"Notification sent to {student['parent_email']}", 'info')
    else:
        flash('Error sending notification', 'danger')
        
    return redirect(url_for('manage_fees'))

# Event Routes
@app.route('/events')
@login_required
def events():
    user_id = session['user_id']
    all_events = db.table('events').all()
    all_events.sort(key=lambda x: x['event_date'])
    for event in all_events:
        registration = db.table('event_registrations').get(
            (where('event_id') == event.doc_id) & (where('student_id') == user_id)
        )
        event['is_registered'] = 1 if registration else 0
        event['id'] = event.doc_id
    return render_template('events.html', events=all_events)

@app.route('/register-event/<int:event_id>')
@login_required
def register_event(event_id):
    if session['role'] != 'student':
        flash('Only students can register for events', 'warning')
        return redirect(url_for('events'))
        
    try:
        existing = db.table('event_registrations').get(
            (where('event_id') == event_id) & (where('student_id') == session['user_id'])
        )
        if existing:
            flash('Already registered!', 'warning')
        else:
            db.table('event_registrations').insert({
                'event_id': event_id,
                'student_id': session['user_id'],
                'registration_date': datetime.datetime.now().isoformat()
            })
            flash('Registered successfully!', 'success')
    except Exception as e:
        flash(f'Error occurred: {str(e)}', 'danger')
    return redirect(url_for('events'))

@app.route('/add-event', methods=['POST'])
@login_required
def add_event():
    if session['role'] not in ['admin', 'faculty']:
        flash('Access denied!', 'danger')
        return redirect(url_for('events'))
        
    db.table('events').insert({
        'title': request.form.get('title'),
        'description': request.form.get('description'),
        'event_date': request.form.get('event_date'),
        'location': request.form.get('location')
    })
    flash('Event added successfully!', 'success')
    return redirect(url_for('events'))

@app.route('/event/<int:event_id>')
@login_required
def event_detail(event_id):
    event = db.table('events').get(doc_id=event_id)
    if not event:
        flash('Event not found!', 'danger')
        return redirect(url_for('events'))
    
    event['id'] = event.doc_id
    registration = db.table('event_registrations').get(
        (where('event_id') == event_id) & (where('student_id') == session['user_id'])
    )
    event['is_registered'] = 1 if registration else 0
    
    # Get all registrants for staff
    registrants = []
    if session['role'] in ['admin', 'faculty']:
        reg_records = db.table('event_registrations').search(where('event_id') == event_id)
        for r in reg_records:
            student = db.table('student_profiles').get(where('user_id') == r['student_id'])
            if student:
                registrants.append(student)
                
    return render_template('event_detail.html', event=event, registrants=registrants)

@app.route('/delete-event/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    if session['role'] not in ['admin', 'faculty']:
        flash('Access denied!', 'danger')
        return redirect(url_for('events'))
        
    db.table('events').remove(doc_ids=[event_id])
    db.table('event_registrations').remove(where('event_id') == event_id)
    flash('Event deleted successfully!', 'success')
    return redirect(url_for('events'))

# Syllabus & Resource Routes
@app.route('/syllabus')
@login_required
def syllabus():
    resources = db.table('syllabus').all()
    # Categorize resources
    notes = [r for r in resources if r['type'] == 'Notes']
    timetables = [r for r in resources if r['type'] == 'Time Table']
    return render_template('syllabus.html', notes=notes, timetables=timetables)

@app.route('/add-resource', methods=['POST'])
@login_required
def add_resource():
    if session['role'] not in ['admin', 'faculty']:
        flash('Access denied!', 'danger')
        return redirect(url_for('syllabus'))
    
    db.table('syllabus').insert({
        'title': request.form.get('title'),
        'type': request.form.get('type'),
        'subject': request.form.get('subject'),
        'link': request.form.get('link') or '#',
        'added_by': session['username'],
        'date': datetime.datetime.now().strftime('%Y-%m-%d')
    })
    flash('Resource added successfully!', 'success')
    return redirect(url_for('syllabus'))

# Admin Routes
@app.route('/add-user', methods=['POST'])
@login_required
@role_required('admin')
def add_user():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    role = request.form.get('role')
    full_name = request.form.get('full_name')
    
    if not all([username, email, password, role, full_name]):
        flash('All basic fields are required!', 'danger')
        return redirect(url_for('admin_panel'))

    if role == 'admin' and db.table('users').get(where('role') == 'admin'):
        flash('Only one admin account is allowed.', 'danger')
        return redirect(url_for('admin_panel'))
    
    # Check if user exists
    if db.table('users').get(User.username == username) or db.table('users').get(where('email') == email):
        flash('Username or Email already exists!', 'danger')
        return redirect(url_for('admin_panel'))
        
    user_id = create_user_account(
        username=username,
        email=email,
        password=password,
        role=role,
        full_name=full_name,
        roll_number=request.form.get('roll_number'),
        department=request.form.get('department') or 'TBD'
    )

    flash(f'User {username} added successfully!', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin-panel')
@login_required
@role_required('admin')
def admin_panel():
    users = db.table('users').all()
    for u in users:
        u['id'] = u.doc_id
    return render_template('admin.html', users=users)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user_id = session['user_id']
    role = session['role']
    
    # Get user account info
    user = db.table('users').get(doc_id=user_id)
    
    # Get/Initialize Profile info
    profile_data = None
    if role == 'student':
        profile_data = db.table('student_profiles').get(where('user_id') == user_id)
        if not profile_data:
            db.table('student_profiles').insert({'user_id': user_id, 'full_name': user['username'], 'roll_number': f'STU{user_id}', 'department': 'General', 'semester': 1})
            profile_data = db.table('student_profiles').get(where('user_id') == user_id)
            
    elif role == 'faculty':
        profile_data = db.table('faculty_profiles').get(where('user_id') == user_id)
        if not profile_data:
            db.table('faculty_profiles').insert({'user_id': user_id, 'full_name': user['username'], 'department': 'General'})
            profile_data = db.table('faculty_profiles').get(where('user_id') == user_id)
            
    elif role == 'admin':
        profile_data = db.table('admin_profiles').get(where('user_id') == user_id)
        if not profile_data:
            db.table('admin_profiles').insert({'user_id': user_id, 'full_name': 'Administrator', 'title': 'System Admin'})
            profile_data = db.table('admin_profiles').get(where('user_id') == user_id)

    if request.method == 'POST':
        # Update User Account info
        new_email = request.form.get('email')
        db.table('users').update({'email': new_email}, doc_ids=[user_id])
        
        # Update Profile info based on role
        if role == 'student':
            db.table('student_profiles').update({
                'full_name': request.form.get('full_name'),
                'roll_number': request.form.get('roll_number'),
                'department': request.form.get('department'),
                'semester': int(request.form.get('semester', 1)),
                'parent_email': request.form.get('parent_email'),
                'parent_phone': request.form.get('parent_phone')
            }, where('user_id') == user_id)
            
        elif role == 'faculty':
            db.table('faculty_profiles').update({
                'full_name': request.form.get('full_name'),
                'department': request.form.get('department'),
                'bio': request.form.get('bio')
            }, where('user_id') == user_id)
            
        elif role == 'admin':
            db.table('admin_profiles').update({
                'full_name': request.form.get('full_name'),
                'title': request.form.get('title')
            }, where('user_id') == user_id)
            
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))

    return render_template('profile.html', user=user, profile=profile_data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
