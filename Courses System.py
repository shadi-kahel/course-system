from flask import Flask, flash, render_template, request, redirect, url_for
from models import Course 
import sqlite3

app = Flask(__name__)
app.secret_key = "my_super_secret_key_12345"
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
            teacher_id INTEGER,
            seats_count INTEGER CHECK (seats_count >= 0),
            FOREIGN KEY (teacher_id) REFERENCES teachers(id)
        )
    """)
    count = conn.execute("SELECT COUNT(*) FROM teachers").fetchone()[0]
    if count == 0:
                     
        conn.commit()
        conn.close()

@app.route('/teachers')
def teachers_list():
    conn = get_db()
    teachers = conn.execute("SELECT * FROM teachers").fetchall()
    conn.close()
    return render_template('teachers.html', teachers=teachers)

@app.route('/new_teachers', methods=['GET', 'POST'])
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
def update_teacher(id):
    with get_db() as conn:
        teacher = conn.execute(
            "SELECT * FROM teachers WHERE id=?",
            (id,)
        ).fetchone()

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
            row["seats_count"]
        )
        courses.append(course)
    return render_template('courses.html', courses=courses)

@app.route('/new', methods=['GET', 'POST'])
def new_course():
    conn = get_db()

    if  request.method == 'POST':
        name = request.form.get('name')
        try:    
            price = int(request.form.get('price') or 0)
            duration = int(request.form.get('duration') or 0)
            seats_count = int(request.form.get('seats_count') or 0)
            teacher_id = request.form.get('teacher_id')
            teacher_id = int(teacher_id) if teacher_id else None
        except ValueError: 
            flash("Invalid input!", "danger")
            return redirect(request.url)  
         
        if price < 0 or duration < 0 or seats_count < 0:
            flash("Negative values are not allowed!", "danger")
            return redirect(url_for('new_course'))
    
        conn.execute("""
            INSERT INTO courses (name, price, teacher_id, duration, seats_count)
            VALUES (?, ?, ?, ?, ?)
        """, (
            name,
            price,
            teacher_id,
            duration,
            seats_count
        ))
        conn.commit()
        conn.close()
        return redirect(url_for('courses_list'))

    teachers = conn.execute("SELECT * FROM teachers").fetchall()
    conn.close()
    return render_template('new.html', teachers=teachers, course=None)

@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update_course(id):
    conn = get_db()

    if  request.method == 'POST':
        name = request.form.get('name')
        try:
            price = int(request.form.get('price') or 0)
            duration = int(request.form.get('duration') or 0)
            seats_count = int(request.form.get('seats_count') or 0)
            teacher_id = int(request.form.get('teacher_id')) if request.form.get('teacher_id') else None
        except ValueError: 
            flash("Invalid input!", "danger")
            return redirect(request.url)  
          
        if price < 0 or duration < 0 or seats_count < 0:
            flash("Negative values are not allowed!", "danger")
            return redirect(url_for('update_course', id=id))
        
        conn.execute("""
            UPDATE courses
            SET name=?, price=?, teacher_id=?, duration=?, seats_count=?
            WHERE id=?
        """, (
            name,
            price,
            teacher_id,
            duration,
            seats_count,
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
def delete_course(id):
    conn = get_db()
    conn.execute("DELETE FROM courses WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('courses_list'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
