from flask import Flask, render_template, request, redirect, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Create upload folder if not exists
if not os.path.exists("static/uploads"):
    os.makedirs("static/uploads")

# Database Setup
def init_db():
    conn = sqlite3.connect("database.db")
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
        email TEXT,
        event_id INTEGER
    )
    """)

    conn.commit()
    conn.close()

init_db()

# Home
@app.route("/")
def home():
    return redirect("/events")

# View All Events
@app.route("/events")
def events():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events")
    data = cursor.fetchall()
    conn.close()
    return render_template("events.html", events=data)

# Event Details
@app.route("/event/<int:event_id>")
def event_details(event_id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events WHERE id=?", (event_id,))
    event = cursor.fetchone()
    conn.close()
    return render_template("event_details.html", event=event)

# Register
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        event_id = request.form["event_id"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO registrations (name, email, event_id) VALUES (?, ?, ?)",
                       (name, email, event_id))
        conn.commit()
        conn.close()
        return redirect("/events")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events")
    events = cursor.fetchall()
    conn.close()

    return render_template("register.html", events=events)

# Admin Login
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin":
            session["admin"] = True
            return redirect("/dashboard")

    return render_template("admin_login.html")

# Admin Dashboard
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "admin" not in session:
        return redirect("/admin")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    if request.method == "POST":
        name = request.form["name"]
        date = request.form["date"]
        venue = request.form["venue"]
        description = request.form["description"]
        image = request.files["image"]

        image_filename = image.filename
        image.save("static/uploads/" + image_filename)

        cursor.execute("""
        INSERT INTO events (name, date, venue, description, image)
        VALUES (?, ?, ?, ?, ?)
        """, (name, date, venue, description, image_filename))

        conn.commit()

    cursor.execute("SELECT COUNT(*) FROM events")
    total_events = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM registrations")
    total_registrations = cursor.fetchone()[0]

    cursor.execute("SELECT * FROM events")
    events = cursor.fetchall()

    conn.close()

    return render_template("admin.html",
                           total_events=total_events,
                           total_registrations=total_registrations,
                           events=events)

# Logout
@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/admin")

if __name__ == "__main__":
    app.run(debug=True)