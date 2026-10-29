"""Team 73 Online Quiz System
Sprint 1: Core Quiz System (S1-01 to S1-14)
Sprint 2: Results, Leaderboard, Admin Content Management, Security (S2-01 to S2-14)
Run:  python3 app.py   then open http://127.0.0.1:5000
"""
import os, re, sqlite3, time
from functools import wraps
from flask import Flask, g, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

BASE = os.path.dirname(__file__)
DB = os.path.join(BASE, "quiz.db")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this-before-submission-team73")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ---------- Database Helpers ----------
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


# ---------- Access Control (REQ-22, REQ-23, TC18) ----------
def login_required(view):
    """Any page wrapped with this needs a logged-in user."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    """S2-06 (REQ-23, TC18): Only authorized administrators can access."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "error")
            return redirect(url_for("login"))
        if session.get("role") != "Administrator":
            flash("Access denied: Administrator privileges required.", "error")
            return redirect(url_for("home"))
        return view(*args, **kwargs)
    return wrapped


# ---------- Sprint 1 Routes (Auth & Navigation) ----------
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

        # S2-12 / TC23: Passwords are protected using secure PBKDF2 hashing
        get_db().execute(
            "INSERT INTO User(name, email, password, role) VALUES (?, ?, ?, 'User')",
            (name, email, generate_password_hash(password, method="pbkdf2:sha256")),
        )
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
    # S1-03 (REQ-01): Show all available quiz categories
    categories = get_db().execute(
        "SELECT category_id, name, description FROM Category ORDER BY name"
    ).fetchall()
    return render_template("home.html", categories=categories)


@app.route("/category/<int:category_id>")
@login_required
def category(category_id):
    # S1-04 (REQ-02): Category selected
    selected = get_db().execute(
        "SELECT category_id, name, description FROM Category WHERE category_id = ?",
        (category_id,),
    ).fetchone()
    if selected is None:
        flash("That category does not exist.", "error")
        return redirect(url_for("home"))

    # S1-05 (REQ-03): Quizzes belonging to selected category
    quizzes = get_db().execute(
        """SELECT q.quiz_id, q.title, q.time_limit, COUNT(qu.question_id) AS question_count
           FROM Quiz q
           LEFT JOIN Question qu ON qu.quiz_id = q.quiz_id
           WHERE q.category_id = ?
           GROUP BY q.quiz_id
           ORDER BY q.title""",
        (category_id,),
    ).fetchall()
    return render_template("category.html", category=selected, quizzes=quizzes)


@app.route("/quiz/<int:quiz_id>")
@login_required
def quiz(quiz_id):
    # S1-06 (REQ-04, REQ-05) & S1-07 (REQ-06)
    db = get_db()
    selected = db.execute(
        """SELECT q.quiz_id, q.title, q.time_limit, q.category_id,
                  c.name AS category_name
           FROM Quiz q
           JOIN Category c ON c.category_id = q.category_id
           WHERE q.quiz_id = ?""",
        (quiz_id,),
    ).fetchone()

    if selected is None:
        flash("That quiz does not exist.", "error")
        return redirect(url_for("home"))

    start_key = f"quiz_started_at_{quiz_id}"
    if start_key not in session:
        session[start_key] = time.time()

    deadline_ms = int(
        (float(session[start_key]) + int(selected["time_limit"]) * 60) * 1000
    )

    questions = db.execute(
        """SELECT question_id, question_text, option_a, option_b,
                  option_c, option_d
           FROM Question
           WHERE quiz_id = ?
           ORDER BY question_id""",
        (quiz_id,),
    ).fetchall()

    return render_template(
        "quiz.html", quiz=selected, questions=questions, deadline_ms=deadline_ms
    )


# ---------- Sprint 2: Rahul's Modules (S2-01 to S2-07) ----------
@app.route("/quiz/<int:quiz_id>/submit", methods=["POST"])
@login_required
def submit_quiz(quiz_id):
    db = get_db()
    quiz_record = db.execute(
        """SELECT q.quiz_id, q.title, q.time_limit, q.category_id,
                  c.name AS category_name
           FROM Quiz q
           JOIN Category c ON c.category_id = q.category_id
           WHERE q.quiz_id = ?""",
        (quiz_id,),
    ).fetchone()

    if quiz_record is None:
        flash("That quiz does not exist.", "error")
        return redirect(url_for("home"))

    # S2-07 / TC17: Prevent duplicate submission and expired session handling
    start_key = f"quiz_started_at_{quiz_id}"
    started_at = session.get(start_key)

    if started_at is None:
        flash("Quiz session already submitted or expired.", "error")
        return redirect(url_for("category", category_id=quiz_record["category_id"]))

    elapsed = max(0, time.time() - float(started_at))
    limit_seconds = int(quiz_record["time_limit"]) * 60
    timed_out = request.form.get("timeout_submission") == "1"

    if elapsed > limit_seconds:
        if not timed_out or elapsed > limit_seconds + 5:
            session.pop(start_key, None)
            flash("Time expired. Late answers were not accepted.", "error")
            return redirect(url_for("category", category_id=quiz_record["category_id"]))

    questions = db.execute(
        """SELECT question_id, question_text, option_a, option_b,
                  option_c, option_d, correct_option
           FROM Question
           WHERE quiz_id = ?
           ORDER BY question_id""",
        (quiz_id,),
    ).fetchall()

    if not questions:
        session.pop(start_key, None)
        flash("This quiz has no questions.", "error")
        return redirect(url_for("category", category_id=quiz_record["category_id"]))

    score = 0
    answers = []
    for q in questions:
        chosen = request.form.get(f"q_{q['question_id']}", "").upper()
        if chosen not in ("A", "B", "C", "D"):
            chosen = ""

        correct = q["correct_option"]
        is_correct = bool(chosen) and chosen == correct
        if is_correct:
            score += 1

        answers.append({
            "question_text": q["question_text"],
            "selected_option": chosen,
            "selected_text": q[f"option_{chosen.lower()}"] if chosen else None,
            "correct_option": correct,
            "correct_text": q[f"option_{correct.lower()}"],
            "is_correct": is_correct,
        })

    actual_time = min(int(elapsed), limit_seconds)

    # Invalidate session token to prevent repeated/duplicate insertion (TC17)
    session.pop(start_key, None)

    # S2-01 (REQ-13, TC16): Insert into Result using schema.sql columns
    cursor = db.execute(
        """INSERT INTO Result (user_id, quiz_id, score, time_taken)
           VALUES (?, ?, ?, ?)""",
        (session["user_id"], quiz_id, score, actual_time),
    )
    db.commit()
    result_id = cursor.lastrowid

    session["latest_answers"] = answers
    return redirect(url_for("quiz_result_report", result_id=result_id))


@app.route("/result/<int:result_id>")
@login_required
def quiz_result_report(result_id):
    """S2-04 (Appendix B, TC13): Detailed Quiz Result Report."""
    db = get_db()
    result = db.execute(
        """SELECT r.result_id, r.score, r.time_taken, r.attempted_on,
                  u.name AS user_name, q.title AS quiz_title, c.name AS category_name,
                  q.quiz_id,
                  (SELECT COUNT(*) FROM Question WHERE quiz_id = q.quiz_id) AS total_questions
           FROM Result r
           JOIN User u ON u.user_id = r.user_id
           JOIN Quiz q ON q.quiz_id = r.quiz_id
           JOIN Category c ON c.category_id = q.category_id
           WHERE r.result_id = ?""",
        (result_id,),
    ).fetchone()

    if result is None:
        flash("Result report not found.", "error")
        return redirect(url_for("home"))

    answers = session.pop("latest_answers", [])
    return render_template("results.html", result=result, answers=answers)


@app.route("/results/history")
@login_required
def user_results_history():
    """TC16: Verify result persistence after re-login."""
    db = get_db()
    results = db.execute(
        """SELECT r.result_id, q.title AS quiz_title, c.name AS category_name,
                  r.score, r.time_taken, r.attempted_on,
                  (SELECT COUNT(*) FROM Question qu WHERE qu.quiz_id = q.quiz_id) AS total_questions
           FROM Result r
           JOIN Quiz q ON q.quiz_id = r.quiz_id
           JOIN Category c ON c.category_id = q.category_id
           WHERE r.user_id = ?
           ORDER BY r.attempted_on DESC""",
        (session["user_id"],),
    ).fetchall()
    return render_template("history.html", results=results)


@app.route("/leaderboard")
@login_required
def leaderboard():
    """S2-02, S2-03 (REQ-14, REQ-15, TC14, TC15):
    Tie-break rule: Highest score first, then lowest time_taken, then earliest attempted_on.
    """
    db = get_db()
    quiz_id = request.args.get("quiz_id", type=int)

    quizzes = db.execute("SELECT quiz_id, title FROM Quiz ORDER BY title").fetchall()

    query = """
        SELECT u.name AS user_name, q.title AS quiz_title,
               r.score, r.time_taken, r.attempted_on,
               (SELECT COUNT(*) FROM Question qu WHERE qu.quiz_id = q.quiz_id) AS total_questions
        FROM Result r
        JOIN User u ON u.user_id = r.user_id
        JOIN Quiz q ON q.quiz_id = r.quiz_id
    """
    params = []
    if quiz_id:
        query += " WHERE r.quiz_id = ?"
        params.append(quiz_id)

    query += " ORDER BY r.score DESC, r.time_taken ASC, r.attempted_on ASC LIMIT 50"

    rankings = db.execute(query, params).fetchall()
    return render_template(
        "leaderboard.html", rankings=rankings, quizzes=quizzes, selected_quiz=quiz_id
    )


# ---------- Sprint 2: Sharanya's Modules (S2-08 to S2-14) ----------
@app.route("/admin")
@admin_required
def admin_dashboard():
    """S2-06 (TC18): Admin portal dashboard."""
    db = get_db()
    quizzes = db.execute(
        """SELECT q.quiz_id, q.title, c.name AS category_name, COUNT(qu.question_id) AS question_count
           FROM Quiz q
           JOIN Category c ON c.category_id = q.category_id
           LEFT JOIN Question qu ON qu.quiz_id = q.quiz_id
           GROUP BY q.quiz_id ORDER BY q.quiz_id DESC"""
    ).fetchall()
    categories = db.execute("SELECT * FROM Category ORDER BY name").fetchall()
    return render_template("admin_dashboard.html", quizzes=quizzes, categories=categories)


@app.route("/admin/category/add", methods=["POST"])
@admin_required
def admin_add_category():
    """S2-11 (REQ-19): Add quiz category."""
    name = request.form.get("name", "").strip()
    desc = request.form.get("description", "").strip()
    if not name:
        flash("Category name is required.", "error")
    else:
        db = get_db()
        try:
            db.execute("INSERT INTO Category (name, description) VALUES (?, ?)", (name, desc))
            db.commit()
            flash(f"Category '{name}' created successfully.", "success")
        except sqlite3.IntegrityError:
            flash(f"Category '{name}' already exists.", "error")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/quiz/<int:quiz_id>/questions")
@admin_required
def admin_manage_questions(quiz_id):
    """View and manage questions for a specific quiz."""
    db = get_db()
    quiz = db.execute("SELECT * FROM Quiz WHERE quiz_id = ?", (quiz_id,)).fetchone()
    if not quiz:
        flash("Quiz not found.", "error")
        return redirect(url_for("admin_dashboard"))

    questions = db.execute(
        "SELECT * FROM Question WHERE quiz_id = ? ORDER BY question_id", (quiz_id,)
    ).fetchall()
    return render_template("admin_questions.html", quiz=quiz, questions=questions)


@app.route("/admin/quiz/<int:quiz_id>/question/add", methods=["POST"])
@admin_required
def admin_add_question(quiz_id):
    """S2-08 (REQ-16, TC19, TC20, TC21): Add question with validation."""
    q_text = request.form.get("question_text", "").strip()
    opt_a = request.form.get("option_a", "").strip()
    opt_b = request.form.get("option_b", "").strip()
    opt_c = request.form.get("option_c", "").strip()
    opt_d = request.form.get("option_d", "").strip()
    correct = request.form.get("correct_option", "").strip().upper()

    if not (q_text and opt_a and opt_b and opt_c and opt_d):
        flash("All question fields and options (A-D) are required.", "error")
        return redirect(url_for("admin_manage_questions", quiz_id=quiz_id))

    if correct not in ("A", "B", "C", "D"):
        flash("Correct option must be one of A, B, C, or D.", "error")
        return redirect(url_for("admin_manage_questions", quiz_id=quiz_id))

    db = get_db()
    db.execute(
        """INSERT INTO Question (quiz_id, question_text, option_a, option_b, option_c, option_d, correct_option)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (quiz_id, q_text, opt_a, opt_b, opt_c, opt_d, correct),
    )
    db.commit()
    flash("Question added successfully.", "success")
    return redirect(url_for("admin_manage_questions", quiz_id=quiz_id))


@app.route("/admin/question/<int:question_id>/edit", methods=["GET", "POST"])
@admin_required
def admin_edit_question(question_id):
    """S2-09 (REQ-17, TC22): Update question."""
    db = get_db()
    q = db.execute("SELECT * FROM Question WHERE question_id = ?", (question_id,)).fetchone()
    if not q:
        flash("Question not found.", "error")
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        q_text = request.form.get("question_text", "").strip()
        opt_a = request.form.get("option_a", "").strip()
        opt_b = request.form.get("option_b", "").strip()
        opt_c = request.form.get("option_c", "").strip()
        opt_d = request.form.get("option_d", "").strip()
        correct = request.form.get("correct_option", "").strip().upper()

        if not (q_text and opt_a and opt_b and opt_c and opt_d) or correct not in ("A", "B", "C", "D"):
            flash("Invalid data: All fields are required and correct option must be A-D.", "error")
            return render_template("edit_question.html", q=q)

        db.execute(
            """UPDATE Question
               SET question_text = ?, option_a = ?, option_b = ?, option_c = ?, option_d = ?, correct_option = ?
               WHERE question_id = ?""",
            (q_text, opt_a, opt_b, opt_c, opt_d, correct, question_id),
        )
        db.commit()
        flash("Question updated successfully.", "success")
        return redirect(url_for("admin_manage_questions", quiz_id=q["quiz_id"]))

    return render_template("edit_question.html", q=q)


@app.route("/admin/question/<int:question_id>/delete", methods=["POST"])
@admin_required
def admin_delete_question(question_id):
    """S2-10 (REQ-18, TC22): Delete question."""
    db = get_db()
    q = db.execute("SELECT quiz_id FROM Question WHERE question_id = ?", (question_id,)).fetchone()
    if q:
        db.execute("DELETE FROM Question WHERE question_id = ?", (question_id,))
        db.commit()
        flash("Question deleted successfully.", "success")
        return redirect(url_for("admin_manage_questions", quiz_id=q["quiz_id"]))

    flash("Question not found.", "error")
    return redirect(url_for("admin_dashboard"))


if __name__ == "__main__":
    app.run(debug=True)