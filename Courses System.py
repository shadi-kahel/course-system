from flask import Flask, flash, render_template, request, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from models import Course 
from flask import session
import sqlite3
import re

app = Flask(__name__)
app.secret_key = "dev-secret-key"
DATABASES = 'courses.db'

def get_db():
    conn = sqlite3.connect(DATABASES)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price INTEGER NOT NULL CHECK (price >= 0), 
            duration INTEGER CHECK (duration >= 0),
            description TEXT,
            teacher_id INTEGER,
            seats_count INTEGER CHECK (seats_count >= 0),
            FOREIGN KEY (teacher_id) REFERENCES teachers(id)
        )
    """)  
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            birth_date TEXT,
            country TEXT
        )
    """)  
    conn.execute("""
        CREATE TABLE IF NOT EXISTS enrollments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(course_id) REFERENCES courses(id),
            UNIQUE(user_id, course_id)  
        )
    """)
    conn.commit()
    conn.close()
        
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        phone = request.form.get('phone')
        birth_date = request.form.get('birth_date')
        country = request.form.get('country')
        if not username or not password:
            flash("All fields are required!", "danger")
            return redirect(request.url)

        hashed_password = generate_password_hash(password)

        try:
            conn = get_db()
            conn.execute(
                "INSERT INTO users (username, password, email, phone, birth_date, country) VALUES (?, ?, ?, ?, ?, ?)",
                (username, hashed_password, email, phone, birth_date, country)
            )
            conn.commit()
            conn.close()
            
        except sqlite3.IntegrityError:
            flash("Username already exists!", "danger")
            return redirect(request.url)

        flash("Registration successful! Please login.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username=?",(username,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash("Login successful!", "success")
            return redirect(url_for('courses_list'))
        
        else:
            flash("Invalid username or password", "danger")
            return redirect(request.url)

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for('login'))        
        
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        
        if 'user_id' not in session:
            flash("Please login first.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if not current_password or not new_password or not confirm_password:
        flash("All fields are required!", "password_error")
        return redirect(url_for('courses_list'))

    if new_password != confirm_password:
        flash("New passwords do not match!", "password_error")
        return redirect(url_for('courses_list'))

    if len(new_password) < 6:
        flash("Password must be at least 6 characters!", "password_error")
        return redirect(url_for('courses_list'))

    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE id=?",
        (session['user_id'],)).fetchone()

    if not check_password_hash(user['password'], current_password):
        conn.close()
        flash("Current password is incorrect!", "password_error")
        return redirect(url_for('courses_list'))

    hashed_password = generate_password_hash(new_password)

    conn.execute(
        "UPDATE users SET password=? WHERE id=?",
        (hashed_password, session['user_id'])
    )
    conn.commit()
    conn.close()

    session.clear()
    flash("Password changed successfully. Please login again.", "success")

    return redirect(url_for('login'))

@app.route('/enroll/<int:course_id>', methods=['POST'])
@login_required
def enroll_course(course_id):
    conn = get_db()
    
    course = conn.execute("SELECT * FROM courses WHERE id=?", (course_id,)).fetchone()
    if not course:
        flash("Course not found.", "danger")
        conn.close()
        return redirect(url_for('courses_list'))
    
    enrollment = conn.execute(
        "SELECT * FROM enrollments WHERE user_id=? AND course_id=?",
        (session['user_id'], course_id)).fetchone()
    
    if enrollment:
        flash("You are already enrolled in this course.", "warning")
        conn.close()
        return redirect(url_for('courses_list'))
    
    conn.execute(
        "INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)",
        (session['user_id'], course_id)
    )
    conn.commit()
    conn.close()
    
    flash(f"You have successfully enrolled in {course['name']}!", "success")
    return redirect(url_for('courses_list'))

@app.route('/unenroll/<int:course_id>', methods=['POST'])
@login_required
def unenroll_course(course_id):
    conn = get_db()
    conn.execute(
        "DELETE FROM enrollments WHERE user_id=? AND course_id=?",
        (session['user_id'], course_id)
    )
    conn.commit()
    conn.close()
    flash("You have successfully unenrolled from the course.", "success")
    return redirect(url_for('my_courses'))

@app.route('/my_courses')
@login_required
def my_courses():
    conn = get_db()
    
    user = conn.execute(
        "SELECT * FROM users WHERE id=?",
        (session['user_id'],)).fetchone()
    
    courses = conn.execute("""
        SELECT courses.*, teachers.name as teacher_name
        FROM courses
        JOIN enrollments ON courses.id = enrollments.course_id
        LEFT JOIN teachers ON courses.teacher_id = teachers.id
        WHERE enrollments.user_id = ?
    """, (session['user_id'],)).fetchall()
    conn.close()
    
    return render_template('my_courses.html', user=user, courses=courses)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    conn = get_db()

    if request.method == 'POST':
        email = request.form.get('email')
        phone = request.form.get('phone')
        birth_date = request.form.get('birth_date')
        country = request.form.get('country')
        
        if phone and not is_valid_phone(phone):           
            flash("Invalid phone number. It must contain 10-15 digits and may start with +", "danger")
            return redirect(url_for('profile'))  
        
        if country and not is_valid_country(country):
            flash("Invalid country. Please select a valid country from the list.", "danger")
            return redirect(url_for('profile'))
    
        conn.execute("""
            UPDATE users
            SET email=?, phone=?, birth_date=?, country=?
            WHERE id=?
        """, (email, phone, birth_date, country, session['user_id']))

        conn.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for('my_courses'))

    user = conn.execute(
        "SELECT * FROM users WHERE id=?",
        (session['user_id'],)
    ).fetchone()

    conn.close()
    return render_template('profile.html', user=user)

def is_valid_phone(phone):
    """
    Checks if the phone number contains only digits,
    optionally starts with +, and length is 10-15 digits
    """
    pattern = r'^(\+?\d{10,15})$'
    return re.match(pattern, phone)

def is_valid_country(country):
    """
    Checks if the given country is in the list of valid countries
    """
    return country in VALID_COUNTRIES

VALID_COUNTRIES = [
    "United States", "Canada", "United Kingdom", "Germany", "France",
    "Italy", "Spain", "Australia", "Egypt", "India", "Japan", "Syria", 
    "Iraq", "United Arab Emirates"
]

@app.route('/teachers')
@login_required
def teachers_list():
    conn = get_db()
    teachers = conn.execute("SELECT * FROM teachers").fetchall()
    conn.close()
    return render_template('teachers.html', teachers=teachers)

@app.route('/new_teachers', methods=['GET', 'POST'])
@login_required
def new_teacher():
    
    if request.method == 'POST':
        conn = get_db()
        conn.execute("""
            INSERT INTO teachers (name, email)
            VALUES (?, ?)
        """, (
            request.form['name'],
            request.form['email']
        ))
        conn.commit()
        conn.close()
        return redirect(url_for('teachers_list'))
    return render_template('new_teacher.html')

@app.route('/update_teacher/<int:id>', methods=['GET', 'POST'])
@login_required
def update_teacher(id):
    
    with get_db() as conn:
        teacher = conn.execute(
            "SELECT * FROM teachers WHERE id=?",(id,)).fetchone()

    if not teacher:
        flash("Teacher not found.", "danger")
        return redirect(url_for('teachers_list'))

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')

        if not name:
            flash("Name is required.", "danger")
            return redirect(request.url)

        with get_db() as conn:
            conn.execute(
                "UPDATE teachers SET name=?, email=? WHERE id=?",
                (name, email, id)
            )

        flash("Teacher updated successfully.", "success")
        return redirect(url_for('teachers_list'))

    return render_template('update_teacher.html', teacher=teacher)

@app.route('/delete_teacher/<int:id>', methods=['POST'])
@login_required
def delete_teacher(id):
    
    with get_db() as conn:
        courses_count = conn.execute(
            "SELECT COUNT(*) FROM courses WHERE teacher_id=?", (id,)).fetchone()[0]

        if courses_count > 0:
            flash("Cannot delete teacher because they have courses.", "danger")
            return redirect(url_for('teachers_list'))

        conn.execute("DELETE FROM teachers WHERE id=?", (id,))
        flash("Teacher deleted successfully.", "success")

    return redirect(url_for('teachers_list'))

@app.route('/')
@login_required
def courses_list():
    conn = get_db()
    rows = conn.execute("""
        SELECT courses.*, teachers.name as teacher_name
        FROM courses
        LEFT JOIN teachers ON courses.teacher_id = teachers.id
    """).fetchall()
    conn.close()
    
    courses = []
    for row in rows:
        course = Course(
            row["id"],
            row["name"],
            row["price"],
            row["teacher_name"],
            row["duration"],
            row["seats_count"],
            row["description"]
        )
        courses.append(course)
    return render_template('courses.html', courses=courses)

@app.route('/new', methods=['GET', 'POST'])
@login_required
def new_course():
    conn = get_db()
       
    if  request.method == 'POST':
        name = request.form.get('name')

        if not name:
            flash("Course name is required!", "danger")
            return redirect(request.url)
        
        try:    
            price = int(request.form.get('price') or 0)
            duration = int(request.form.get('duration') or 0)
            seats_count = int(request.form.get('seats_count') or 0)
            teacher_id = request.form.get('teacher_id')
            teacher_id = int(teacher_id) if teacher_id else None
            description = request.form.get('description')
            
        except ValueError: 
            flash("Invalid input!", "danger")
            return redirect(request.url)  
         
        if price < 0 or duration < 0 or seats_count < 0:
            flash("Negative values are not allowed!", "danger")
            return redirect(url_for('new_course'))
    
        conn.execute("""
            INSERT INTO courses (name, price, teacher_id, duration, seats_count, description)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            name,
            price,
            teacher_id,
            duration,
            seats_count,
            description
        ))
        conn.commit()
        conn.close()
        return redirect(url_for('courses_list'))

    teachers = conn.execute("SELECT * FROM teachers").fetchall()
    conn.close()
    return render_template('new.html', teachers=teachers, course=None)

@app.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update_course(id):
    conn = get_db()
    
    if  request.method == 'POST':
        name = request.form.get('name')

        if not name:
            flash("Course name is required!", "danger")
            return redirect(request.url)
        
        try:
            price = int(request.form.get('price') or 0)
            duration = int(request.form.get('duration') or 0)
            seats_count = int(request.form.get('seats_count') or 0)
            teacher_id = int(request.form.get('teacher_id')) if request.form.get('teacher_id') else None
            description = request.form.get('description')
            
        except ValueError: 
            flash("Invalid input!", "danger")
            return redirect(request.url)  
          
        if price < 0 or duration < 0 or seats_count < 0:
            flash("Negative values are not allowed!", "danger")
            return redirect(url_for('update_course', id=id))
        
        conn.execute("""
            UPDATE courses
            SET name=?, price=?, teacher_id=?, duration=?, seats_count=?, description=?
            WHERE id=?
        """, (
            name,
            price,
            teacher_id,
            duration,
            seats_count,
            description,
            id
        ))
        conn.commit()
        conn.close()
        return redirect(url_for('courses_list'))

    course = conn.execute(
        "SELECT * FROM courses WHERE id=?", (id,)).fetchone()
    teachers = conn.execute("SELECT * FROM teachers").fetchall()
    conn.close()
    
    return render_template('update.html', course=course, teachers=teachers)

@app.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_course(id):
    conn = get_db()
    conn.execute("DELETE FROM courses WHERE id=?", (id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for('courses_list'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
