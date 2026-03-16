from flask import Flask, render_template, request, redirect, session
import sqlite3
import os

def get_db_connection():
    # Use /tmp for writable storage on Render
    db_path = os.path.join("/tmp", "database.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Use /tmp for uploads on Render (persistent during runtime)
upload_folder = os.path.join("/tmp", "uploads")
os.makedirs(upload_folder, exist_ok=True)

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
    conn.close()
    return render_template("home.html", events=events)

@app.route("/events")
def events():
    search_query = request.args.get("search")

    conn = get_db_connection()
    cursor = conn.cursor()

    if search_query:
        cursor.execute("""
            SELECT * FROM events
            WHERE name LIKE ? OR venue LIKE ?
        """, (f"%{search_query}%", f"%{search_query}%"))
    else:
        cursor.execute("SELECT * FROM events")

    data = cursor.fetchall()
    conn.close()

    return render_template("events.html", events=data)

@app.route("/event/<int:event_id>")
def event_details(event_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events WHERE id=?", (event_id,))
    event = cursor.fetchone()
    conn.close()

    if event is None:
        return redirect("/events")

    return render_template("event_details.html", event=event)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        event_id = request.form["event_id"]

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
        username = request.form["username"]
        password = request.form["password"]

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
        name = request.form["name"]
        date = request.form["date"]
        venue = request.form["venue"]
        description = request.form["description"]
        image = request.files.get("image")
        image_filename = ""

        if image and image.filename != "":
            image_filename = image.filename
            image_path = os.path.join(upload_folder, image_filename)
            image.save(image_path)

        cursor.execute("""
            INSERT INTO events (name, date, venue, description, image)
            VALUES (?, ?, ?, ?, ?)
        """, (name, date, venue, description, image_filename))

        conn.commit()

    cursor.execute("SELECT COUNT(*) as total FROM events")
    total_events = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as total FROM registrations")
    total_registrations = cursor.fetchone()["total"]

    cursor.execute("SELECT * FROM events")
    events = cursor.fetchall()

    conn.close()

    return render_template(
        "admin.html",
        total_events=total_events,
        total_registrations=total_registrations,
        events=events
    )

@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/admin")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))

    app.run(host="0.0.0.0", port=port, debug=False)