"""Team 73 Online Quiz System
S1-02: User registration, login, logout (REQ-22)
S1-03: Display quiz categories on the home page (REQ-01)
S1-04: Select a quiz category (REQ-02)
S1-05: Display the quizzes of the selected category (REQ-03)
S1-06: Display the questions and answer options of a quiz (REQ-04, REQ-05)
Run:  python app.py   then open http://127.0.0.1:5000
"""
import os, re, sqlite3
from functools import wraps
from flask import Flask, g, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

BASE = os.path.dirname(__file__)
DB = os.path.join(BASE, "quiz.db")

app = Flask(__name__)
app.secret_key = "change-this-before-submission"   # needed for sessions

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ---------- database helpers ----------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


# ---------- access control (REQ-22) ----------
def login_required(view):
    """Any page wrapped with this needs a logged-in user."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


# ---------- routes ----------
@app.route("/")
def index():
    return redirect(url_for("home") if "user_id" in session else url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        error = None
        if not name or not email or not password:
            error = "All fields are required."
        elif len(name) > 100 or len(email) > 100:
            error = "Name and email must be at most 100 characters."
        elif not EMAIL_RE.match(email):
            error = "Please enter a valid email address."
        elif len(password) < 6:
            error = "Password must be at least 6 characters."
        elif password != confirm:
            error = "Passwords do not match."
        elif get_db().execute("SELECT 1 FROM User WHERE email = ?", (email,)).fetchone():
            error = "An account with this email already exists."

        if error:
            flash(error, "error")
            return render_template("register.html", name=name, email=email)

        # role is always 'User'. Administrators are created by the database seed only.
        get_db().execute(
            "INSERT INTO User(name, email, password, role) VALUES (?, ?, ?, 'User')",
            (name, email, generate_password_hash(password)))
        get_db().commit()
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html", name="", email="")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = get_db().execute("SELECT * FROM User WHERE email = ?", (email,)).fetchone()

        # same message for wrong email or wrong password (do not reveal which)
        if user is None or not check_password_hash(user["password"], password):
            flash("Invalid email or password.", "error")
            return render_template("login.html", email=email)

        session.clear()
        session["user_id"] = user["user_id"]
        session["name"] = user["name"]
        session["role"] = user["role"]
        return redirect(url_for("home"))

    return render_template("login.html", email="")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


@app.route("/home")
@login_required
def home():
    # S1-03 (REQ-01): show all available quiz categories
    categories = get_db().execute(
        "SELECT category_id, name, description FROM Category ORDER BY name"
    ).fetchall()
    return render_template("home.html", categories=categories)


@app.route("/category/<int:category_id>")
@login_required
def category(category_id):
    # S1-04 (REQ-02): the selected category is identified by its id in the URL
    selected = get_db().execute(
        "SELECT category_id, name, description FROM Category WHERE category_id = ?",
        (category_id,)).fetchone()
    if selected is None:
        flash("That category does not exist.", "error")
        return redirect(url_for("home"))
    # S1-05 (REQ-03): quizzes that belong to the selected category
    quizzes = get_db().execute(
        """SELECT q.quiz_id, q.title, q.time_limit, COUNT(qu.question_id) AS question_count
           FROM Quiz q
           LEFT JOIN Question qu ON qu.quiz_id = q.quiz_id
           WHERE q.category_id = ?
           GROUP BY q.quiz_id
           ORDER BY q.title""", (category_id,)).fetchall()
    return render_template("category.html", category=selected, quizzes=quizzes)


@app.route("/quiz/<int:quiz_id>")
@login_required
def quiz(quiz_id):
    # S1-06 (REQ-04, REQ-05): show the questions of the selected quiz, 4 options each
    selected = get_db().execute(
        """SELECT q.quiz_id, q.title, q.time_limit, q.category_id, c.name AS category_name
           FROM Quiz q JOIN Category c ON c.category_id = q.category_id
           WHERE q.quiz_id = ?""", (quiz_id,)).fetchone()
    if selected is None:
        flash("That quiz does not exist.", "error")
        return redirect(url_for("home"))

    # NOTE: correct_option is deliberately NOT selected, so the answer never reaches
    # the browser. Scoring is done on the server (S1-10).
    questions = get_db().execute(
        """SELECT question_id, question_text, option_a, option_b, option_c, option_d
           FROM Question WHERE quiz_id = ? ORDER BY question_id""", (quiz_id,)).fetchall()
    return render_template("quiz.html", quiz=selected, questions=questions)


@app.route("/quiz/<int:quiz_id>/submit", methods=["POST"])
@login_required
def submit_quiz(quiz_id):
    # PLACEHOLDER: S1-07 (timer), S1-08 (record answers) and S1-10 (scoring)
    # replace this stub. Radio inputs are named "q_<question_id>" with value A/B/C/D.
    flash("Submitting answers is not implemented yet (S1-08).", "error")
    return redirect(url_for("quiz", quiz_id=quiz_id))


if __name__ == "__main__":
    app.run(debug=True)
