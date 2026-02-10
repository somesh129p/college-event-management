from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secret"


def init_db():
    conn = sqlite3.connect("database.db")
    
    conn.execute("""
    CREATE TABLE IF NOT EXISTS events(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        date TEXT,
        venue TEXT
    )
    """)
    
    conn.execute("""
    CREATE TABLE IF NOT EXISTS registrations(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student TEXT,
        event TEXT
    )
    """)
    
    conn.close()

init_db()

@app.route("/")
def home():
    return render_template("home.html")


@app.route("/events")
def events():
    conn = sqlite3.connect("database.db")
    data = conn.execute("SELECT * FROM events").fetchall()
    conn.close()
    return render_template("events.html", events=data)


@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        student = request.form["student"]
        event = request.form["event"]
        
        conn = sqlite3.connect("database.db")
        conn.execute("INSERT INTO registrations(student,event) VALUES (?,?)",(student,event))
        conn.commit()
        conn.close()
        
        return redirect("/events")
    
    return render_template("register.html")

@app.route("/admin", methods=["GET","POST"])
def admin():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        if username == "admin" and password == "admin":
            session["admin"] = True
            return redirect("/dashboard")
    
    return render_template("admin_login.html")


@app.route("/dashboard", methods=["GET","POST"])
def dashboard():
    if "admin" not in session:
        return redirect("/admin")
    
    if request.method == "POST":
        name = request.form["name"]
        date = request.form["date"]
        venue = request.form["venue"]
        
        conn = sqlite3.connect("database.db")
        conn.execute("INSERT INTO events(name,date,venue) VALUES (?,?,?)",(name,date,venue))
        conn.commit()
        conn.close()
    
    conn = sqlite3.connect("database.db")
    events = conn.execute("SELECT * FROM events").fetchall()
    conn.close()
    
    return render_template("admin_dashboard.html", events=events)

# Delete Event
@app.route("/delete_event/<int:event_id>")
def delete_event(event_id):
    if "admin" not in session:
        return redirect("/admin")

    conn = sqlite3.connect("database.db")
    conn.execute("DELETE FROM events WHERE id=?", (event_id,))
    conn.commit()
    conn.close()

    return redirect("/dashboard")


# View Registrations
@app.route("/registrations")
def registrations():
    if "admin" not in session:
        return redirect("/admin")

    conn = sqlite3.connect("database.db")
    data = conn.execute("SELECT * FROM registrations").fetchall()
    conn.close()

    return render_template("registrations.html", registrations=data)


# Logout
@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/")

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)