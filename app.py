from flask import Flask, render_template, request, redirect, session
from datetime import date
from werkzeug.utils import secure_filename
import sqlite3
import os
import pandas as pd
from flask import send_file

SECURITY_ANSWER = "somesh123"

app = Flask(__name__)
app.secret_key = "secret"

UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db_connection():
    db_path = os.path.join(app.root_path, "database.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        date TEXT,
        venue TEXT,
        description TEXT,
        image TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS registrations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        roll_no TEXT,
        department TEXT,
        class_name TEXT,
        mobile TEXT,
        email TEXT,
        event_id INTEGER
    )
    """)

    conn.commit()
    conn.close()

init_db()

@app.route("/")
def home():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM events LIMIT 3")
    events = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) as total FROM events")
    total_events = cursor.fetchone()["total"]

    conn.close()
    return render_template("home.html", events=events, total_events=total_events)

@app.route("/events")
def events():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM events")
    events = cursor.fetchall()

    conn.close()
    return render_template("events.html", events=events)

@app.route("/event/<int:id>")
def event_details(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM events WHERE id=?", (id,))
    event = cursor.fetchone()

    conn.close()
    return render_template("event_details.html", event=event)

@app.route("/register", methods=["GET", "POST"])
def register():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        name = request.form.get("name")
        roll_no = request.form.get("roll_no")
        department = request.form.get("department")
        class_name = request.form.get("class_name")
        mobile = request.form.get("mobile")
        email = request.form.get("email")
        event_id = request.form.get("event_id")

        if name and roll_no and department and class_name and mobile and email and event_id:
            cursor.execute("""
                INSERT INTO registrations
                (name, roll_no, department, class_name, mobile, email, event_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (name, roll_no, department, class_name, mobile, email, event_id))
            conn.commit()

        conn.close()
        return redirect("/events")

    cursor.execute("SELECT * FROM events")
    events = cursor.fetchall()

    conn.close()
    return render_template("register.html", events=events)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        saved_password = session.get("admin_password", "admin")

        if username == "admin" and password == saved_password:
            session["admin"] = True
            return redirect("/dashboard")

    return render_template("admin_login.html")

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if not session.get("admin"):
        return redirect("/admin")

    conn = get_db_connection()
    cursor = conn.cursor()

    today = date.today().isoformat()

    if request.method == "POST":
        name = request.form.get("name")
        event_date = request.form.get("date")
        venue = request.form.get("venue")
        description = request.form.get("description")
        image = request.files.get("image")

        filename = None
        if image and image.filename != "":
            filename = secure_filename(image.filename)
            image.save(os.path.join(UPLOAD_FOLDER, filename))

        if name and event_date and venue and event_date >= today:
            cursor.execute("""
                INSERT INTO events (name, date, venue, description, image)
                VALUES (?, ?, ?, ?, ?)
            """, (name, event_date, venue, description, filename))
            conn.commit()

    cursor.execute("SELECT * FROM events")
    events = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) as total FROM events")
    total_events = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as total FROM registrations")
    total_registrations = cursor.fetchone()["total"]

    search = request.args.get("search")

    if search:
        cursor.execute("""
            SELECT 
                registrations.id as reg_id,
                registrations.name as student_name,
                registrations.roll_no,
                registrations.department,
                registrations.class_name,
                registrations.mobile,
                registrations.email,
                (SELECT name FROM events WHERE id = registrations.event_id) as event_name
            FROM registrations
            WHERE registrations.name LIKE ? OR registrations.email LIKE ?
        """, ('%' + search + '%', '%' + search + '%'))
    else:
        cursor.execute("""
            SELECT 
                registrations.id as reg_id,
                registrations.name as student_name,
                registrations.roll_no,
                registrations.department,
                registrations.class_name,
                registrations.mobile,
                registrations.email,
                (SELECT name FROM events WHERE id = registrations.event_id) as event_name
            FROM registrations
        """)

    students = cursor.fetchall()

    cursor.execute("""
    SELECT events.id, events.name, COUNT(registrations.id) as total_students
    FROM events
    LEFT JOIN registrations ON events.id = registrations.event_id
    GROUP BY events.id, events.name
    """)
    event_counts = cursor.fetchall()

    cursor.execute("""
    SELECT events.name as event_name, registrations.name as student_name
    FROM registrations
    LEFT JOIN events ON registrations.event_id = events.id
    ORDER BY events.name
    """)
    event_students = cursor.fetchall()

    conn.close()

    return render_template(
        "admin_dashboard.html",
        events=events,
        total_events=total_events,
        total_registrations=total_registrations,
        students=students,
        today=today,
        event_counts=event_counts,
        event_students=event_students
    )

@app.route("/delete_event/<int:id>")
def delete_event(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM registrations WHERE event_id=?", (id,))
    cursor.execute("DELETE FROM events WHERE id=?", (id,))

    conn.commit()
    conn.close()
    return redirect("/dashboard")

@app.route("/delete_registration/<int:id>")
def delete_registration(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM registrations WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/dashboard")

@app.route("/delete_all_registrations")
def delete_all_registrations():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM registrations")
    conn.commit()
    conn.close()
    return redirect("/dashboard")

@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/admin")

@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        username = request.form.get("username")
        answer = request.form.get("answer")
        new_password = request.form.get("new_password")

        if username == "admin" and answer == SECURITY_ANSWER:
            session["admin_password"] = new_password
            return redirect("/admin")
        else:
            return "Wrong username or answer"

    return render_template("forgot_password.html")


@app.route("/export_excel")
def export_excel():
    if not session.get("admin"):
        return redirect("/admin")

    conn = get_db_connection()

    df = pd.read_sql_query("""
        SELECT 
            registrations.name AS Student_Name,
            registrations.email AS Email,
            events.name AS Event_Name
        FROM registrations
        LEFT JOIN events ON registrations.event_id = events.id
    """, conn)

    conn.close()

    file_path = "registered_students.xlsx"
    df.to_excel(file_path, index=False)

    return send_file(file_path, as_attachment=True)

@app.route("/export_event_excel")
def export_event_excel():
    if not session.get("admin"):
        return redirect("/admin")

    conn = get_db_connection()

    df = pd.read_sql_query("""
        SELECT 
            events.name AS Event_Name,
            registrations.name AS Student_Name,
            registrations.roll_no AS Roll_No,
            registrations.department AS Department,
            registrations.class_name AS Class,
            registrations.mobile AS Mobile_No,
            registrations.email AS Email
        FROM registrations
        LEFT JOIN events ON registrations.event_id = events.id
        ORDER BY events.name, registrations.name
    """, conn)

    conn.close()

    file_path = "event_wise_registrations.xlsx"
    df.to_excel(file_path, index=False)

    return send_file(file_path, as_attachment=True)

PORT = int(os.environ.get("PORT", 10000))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)