from flask import Flask, render_template, request, redirect, flash, session, send_file
from database import get_db
from face_engine import recognize
import subprocess
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "attendance_secret_key"


# ==========================================
# HOME
# ==========================================
@app.route('/')
def home():
    return render_template("index.html")


# ==========================================
# ADMIN LOGIN PAGE
# ==========================================
@app.route('/admin_login')
def admin_login():
    return render_template("admin_login.html")


# ==========================================
# STUDENT LOGIN PAGE
# ==========================================
@app.route('/student_login')
def student_login():
    return render_template("student_login.html")


# ==========================================
# STUDENT REGISTER PAGE
# ==========================================
@app.route('/student_register')
def student_register():
    return render_template("register.html")


# ==========================================
# DASHBOARD
# ==========================================
@app.route('/student_dashboard')
def student_dashboard():

    print("Dashboard Session:", dict(session))

    if 'student' not in session:
        print("Session Missing")
        return redirect('/student_login')

    return render_template("student_dashboard.html")
# ==========================================
# MARK ATTENDANCE
# ==========================================

@app.route('/mark_attendance')
def mark_attendance():

    if 'student' not in session:
        return redirect('/student_login')

    student_id = int(session['student'])

    db = get_db()
    cur = db.cursor()

    cur.execute(
        "SELECT name FROM students WHERE id=%s",
        (student_id,)
    )

    student = cur.fetchone()

    if not student:
        flash("Student Not Found!")
        return redirect('/student_dashboard')

    name = student[0]

    now = datetime.now()

    cur.execute("""
        INSERT INTO attendance
        (student_id, name, date, time)
        VALUES(%s,%s,%s,%s)
    """, (
        student_id,
        name,
        now.strftime("%Y-%m-%d"),
        now.strftime("%H:%M:%S")
    ))

    db.commit()

    flash("Attendance Marked Successfully!")

    return redirect('/student_dashboard')
# ==========================================
# ADMIN LOGIN CHECK
# ==========================================
@app.route('/login', methods=['POST'])
def do_login():
    username = request.form['username']
    password = request.form['password']

    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT * FROM users WHERE username=%s AND password=%s",
                (username, password))

    user = cur.fetchone()

    if user:
        session['admin'] = username
        flash("Admin Login Successful!")
        return redirect('/admin_dashboard')

    return "Invalid credentials"


# ==========================================
# ADMIN DASHBOARD
# ==========================================
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin' not in session:
        return redirect('/admin_login')

    return render_template("admin_dashboard.html")



# ==========================================
# VIEW ATTENDANCE (ONLY ONE VERSION)
# ==========================================
@app.route('/view_attendance')
def view_attendance():

    if 'admin' not in session:
        return redirect('/admin_login')

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT student_id,name,date,time
        FROM attendance
        ORDER BY date DESC,time DESC
    """)

    data = cur.fetchall()

    return render_template("view.html", data=data)
    print(data)

# ==========================================
# STUDENT LOGIN CHECK
# ==========================================
@app.route('/student_login_check', methods=['POST'])
def student_login_check():

    student_id = request.form['id']
    password = request.form['password']

    db = get_db()
    cur = db.cursor()

    cur.execute(
        """
        SELECT * FROM students
        WHERE id=%s AND password=%s
        """,
        (student_id, password)
    )

    student = cur.fetchone()

    if student:
        session['student'] = student_id
        flash("Login Successful!", "success")
        return redirect('/student_dashboard')

    flash("Invalid Login!", "error")
    return redirect('/student_login')


# ==========================================
# SAVE STUDENT + FACE CAPTURE
# ==========================================
@app.route('/save_student', methods=['POST'])
def save_student():

    student_id = request.form['id']
    name = request.form['name']
    password = request.form['password']

    db = get_db()
    cur = db.cursor()

    # Check Duplicate Student
    cur.execute(
        "SELECT * FROM students WHERE id=%s",
        (student_id,)
    )

    if cur.fetchone():
        flash("Student Already Exists!", "error")
        return redirect('/student_register')

    # Save Student
    cur.execute(
        """
        INSERT INTO students(id,name,password)
        VALUES(%s,%s,%s)
        """,
        (student_id, name, password)
    )

    db.commit()

    # Face Capture
    result = subprocess.run(
        ["python", "capture.py", str(student_id)]
    )

    if result.returncode != 0:
        flash("Face Capture Failed!", "error")
        return redirect('/student_register')

    # Create Student Session
    session['student'] = student_id

    flash("Registration Successful!", "success")

    return redirect('/student_dashboard')
    
# ==========================================
# STUDENT MANAGEMENT
# ==========================================
@app.route('/students')
def students():
    if 'admin' not in session:
        return redirect('/admin_login')

    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT id, name, password FROM students")
    data = cur.fetchall()

    return render_template("students.html", data=data)


# ==========================================
# EDIT STUDENT
# ==========================================
@app.route('/edit_student/<id>')
def edit_student(id):
    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT * FROM students WHERE id=%s", (id,))
    student = cur.fetchone()

    return render_template("edit_student.html", student=student)


# ==========================================
# UPDATE STUDENT
# ==========================================
@app.route('/update_student', methods=['POST'])
def update_student():
    id = request.form['id']
    name = request.form['name']
    password = request.form['password']

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        UPDATE students
        SET name=%s, password=%s
        WHERE id=%s
    """, (name, password, id))

    db.commit()

    return redirect('/students')


# ==========================================
# DELETE STUDENT
# ==========================================
@app.route('/delete_student/<id>')
def delete_student(id):
    if 'admin' not in session:
        return redirect('/admin_login')

    db = get_db()
    cur = db.cursor()

    cur.execute("DELETE FROM students WHERE id=%s", (id,))
    db.commit()

    return redirect('/students')


# ==========================================
# FACE LOGIN
# ==========================================
# ==========================================
# FACE LOGIN
# ==========================================
@app.route('/face_student_login')
def face_student_login():

    student_id = recognize()

    print("Recognized Student:", student_id)

    if student_id is None:
        flash("Face not recognized!", "danger")
        return redirect('/student_login')

    session['student'] = str(student_id)

    print("Session:", dict(session))

    db = get_db()
    cur = db.cursor()

    cur.execute(
        "SELECT name FROM students WHERE id=%s",
        (student_id,)
    )

    student = cur.fetchone()

    print("Student:", student)

    if student is None:
        flash("Student not found!", "danger")
        return redirect('/student_login')

    name = student[0]

    now = datetime.now()

    try:
        cur.execute("""
            SELECT id
            FROM attendance
            WHERE student_id=%s AND date=%s
        """, (
            student_id,
            now.strftime("%Y-%m-%d")
        ))

        exists = cur.fetchone()

        if exists is None:

            cur.execute("""
                INSERT INTO attendance
                (student_id,name,date,time)
                VALUES(%s,%s,%s,%s)
            """, (
                student_id,
                name,
                now.strftime("%Y-%m-%d"),
                now.strftime("%H:%M:%S")
            ))

            db.commit()

            print("Attendance Saved")

    except Exception as e:
        print("Attendance Error:", e)

    flash("Face Login Successful!", "success")

    return redirect('/student_dashboard')
# ==========================================
# DOWNLOAD PDF
# ==========================================
@app.route('/download_pdf')
def download_pdf():
    if 'admin' not in session:
        return "Access Denied"

    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT student_id, name, date, time FROM attendance")
    records = cur.fetchall()

    file = "attendance.pdf"
    doc = SimpleDocTemplate(file)

    data = [["ID", "Name", "Date", "Time"]]
    for r in records:
        data.append(list(r))

    table = Table(data)
    table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey)
    ]))

    doc.build([table])

    return send_file(file, as_attachment=True)


# ==========================================
# DOWNLOAD EXCEL
# ==========================================
@app.route('/download_excel')
def download_excel():

    if 'admin' not in session:
        return "Access Denied"

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT student_id, name,
               DATE_FORMAT(date,'%Y-%m-%d'),
               TIME_FORMAT(time,'%H:%i:%s')
        FROM attendance
    """)

    data = cur.fetchall()

    df = pd.DataFrame(
        data,
        columns=["Student ID", "Name", "Date", "Time"]
    )

    file = "attendance.xlsx"

    with pd.ExcelWriter(file, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)

    return send_file(file, as_attachment=True)
# ==========================================
# LOGOUT (ONLY ONE)
# ==========================================
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/student_logout')
def student_logout():
      session.pop('student', None)
      return redirect('/student_login')

# ==========================================
# STUDENT ATTENDANCE
# ==========================================
@app.route('/student_attendance')
def student_attendance():

    if 'student' not in session:
        return redirect('/student_login')

    student_id = int(session['student'])

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT student_id, name, date, time
        FROM attendance
        WHERE student_id=%s
        ORDER BY id DESC
    """, (student_id,))

    data = cur.fetchall()

    return render_template(
        "student_attendance.html",
        data=data
    )
@app.route('/attendance_report')
def attendance_report():

    if 'admin' not in session:
        return redirect('/admin_login')

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT student_id, name, date, time
        FROM attendance
        ORDER BY date DESC, time DESC
    """)

    data = cur.fetchall()

    return render_template(
        "attendance_report.html",
        data=data
    )
# ==========================================
# RUN APP
# ==========================================
if __name__ == "__main__":
    app.run(debug=True)