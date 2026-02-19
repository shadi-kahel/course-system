# from flask import Flask, request, redirect, render_template, url_for

# app = Flask(__name__)
# courses = [ {'id': 0, 'name': 'Python', 'price': 0, 'teacher': '', 'duration': 0, 'seats_count': 0},
            # {'id': 1, 'name': 'HTML', 'price': 0, 'teacher': '', 'duration': 0, 'seats_count': 0},
#             {'id': 2, 'name': 'PHP', 'price': 0, 'teacher': '', 'duration': 0, 'seats_count': 0},
#             {'id': 3, 'name': 'CSS', 'price': 0, 'teacher': '', 'duration': 0, 'seats_count': 0},
            # {'id': 4, 'name': 'JS', 'price': 0, 'teacher': '', 'duration': 0, 'seats_count': 0},
# ]

# @app.route('/')
# def courses_list():
#     return render_template('courses.html', courses=courses)  

# @app.route('/new_course.html', methods=['GET', 'POST'])
# def new_course():
#     if request.method == 'POST':
#         course = {'id': len(courses),
#                   'name': request.form['name'],
#                   'price': int (request.form['price']),
#                   'teacher': request.form['teacher'],
#                   'duration': int (request.form['duration']),
#                   'seats_count': int (request.form['seats_count'])
#         }
#         courses.append(course)
#         return redirect(url_for('courses_list'))
#     return render_template('new.html')

# @app.route('/update/<int:id>', methods=['GET', 'POST'])
# def update_course(id):
#     course = courses[id]
#     if request.method == 'POST':
#         course['name'] = request.form['name']
#         course['price'] = request.form['price']
#         course['teacher'] = request.form['teacher']
#         course['duration'] = request.form['duration']
#         course['seats_count'] = request.form['seats_count']
#         return redirect(url_for('courses_list'))
#     return render_template('update.html', course=course)  

# @app.route('/delete/<int:id>', methods=['POST'])
# def delete_course(id):
#     courses.pop(id)
#     return redirect(url_for('courses_list'))

# if __name__ == '__main__':   
#     app.run(debug=True, port=5000)
    
    
    
from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)
DATABASES = 'courses.db'

def get_db():
    conn = sqlite3.connect(DATABASES)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price INTEGER, 
            teacher TEXT,
            duration INTEGER,
            seats_count INTEGER
        )
    """)
    conn.commit()
    conn.close()

@app.route('/')
def courses_list():
    conn = get_db()
    courses = conn.execute("SELECT * FROM courses").fetchall()
    conn.close()
    return render_template('courses.html', courses=courses)

@app.route('/new', methods=['GET', 'POST'])
def new_course():
    if request.method == 'POST':
        conn = get_db()
        conn.execute("""
            INSERT INTO courses (name, price, teacher, duration, seats_count)
            VALUES (?, ?, ?, ?, ?)
        """, (
            request.form['name'],
            request.form['price'],
            request.form['teacher'],
            request.form['duration'],
            request.form['seats_count']
        ))
        conn.commit()
        conn.close()
        return redirect(url_for('courses_list'))

    return render_template('new.html')

@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update_course(id):
    conn = get_db()

    if request.method == 'POST':
        conn.execute("""
            UPDATE courses
            SET name=?, price=?, teacher=?, duration=?, seats_count=?
            WHERE id=[id]
        """, (
            request.form['name'],
            request.form['price'],
            request.form['teacher'],
            request.form['duration'],
            request.form['seats_count'],
            id
        ))
        conn.commit()
        conn.close()
        return redirect(url_for('courses_list'))

    course = conn.execute(
        "SELECT * FROM courses WHERE id=[id]", (id,)
    ).fetchone()
    conn.close()
    return render_template('update.html', course=course)

@app.route('/delete/<int:id>', methods=['POST'])
def delete_course(id):
    conn = get_db()
    conn.execute("DELETE FROM courses WHERE id=[id]", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('courses_list'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
