from flask import Flask, render_template, request, redirect, session
from werkzeug.utils import secure_filename
import sqlite3
import os

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

    try:
        cursor.execute("ALTER TABLE events ADD COLUMN description TEXT")
    except:
        pass

    try:
        cursor.execute("ALTER TABLE events ADD COLUMN image TEXT")
    except:
        pass

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS registrations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
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
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        event_id = request.form.get("event_id")

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO registrations (name, email, event_id) VALUES (?, ?, ?)",
            (name, email, event_id)
        )

        conn.commit()
        conn.close()

        return redirect("/events")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events")
    events = cursor.fetchall()
    conn.close()

    return render_template("register.html", events=events)


@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == "admin" and password == "admin":
            session["admin"] = True
            return redirect("/dashboard")

    return render_template("admin_login.html")


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if not session.get("admin"):
        return redirect("/admin")

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        name = request.form.get("name")
        date = request.form.get("date")
        venue = request.form.get("venue")
        description = request.form.get("description")
        image = request.files.get("image")

        filename = ""

        if image and image.filename != "":
            filename = secure_filename(image.filename)
            image.save(os.path.join(UPLOAD_FOLDER, filename))

        cursor.execute("""
            INSERT INTO events (name, date, venue, description, image)
            VALUES (?, ?, ?, ?, ?)
        """, (name, date, venue, description, filename))

        conn.commit()

    cursor.execute("SELECT * FROM events")
    events = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) as total FROM events")
    total_events = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as total FROM registrations")
    total_registrations = cursor.fetchone()["total"]

    conn.close()

    return render_template(
        "admin_dashboard.html",
        events=events,
        total_events=total_events,
        total_registrations=total_registrations
    )

@app.route("/registrations")
def view_registrations():
    if not session.get("admin"):
        return redirect("/admin")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT registrations.name, registrations.email, events.name
        FROM registrations
        JOIN events ON registrations.event_id = events.id
    """)

    registrations = cursor.fetchall()

    conn.close()

    return render_template("registrations.html", registrations=registrations)

@app.route("/delete_event/<int:id>")
def delete_event(id):
    conn = get_db_connection()
    cursor = conn.cursor()

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

    return redirect("/registrations")

@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/admin")


PORT = int(os.environ.get("PORT", 10000))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT) 