"""Shared fixtures: every test gets a fresh SQLite database built from schema.sql."""
import os
import sqlite3
import sys

import pytest
from werkzeug.security import generate_password_hash

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, APP_DIR)

import app as quiz_app  # noqa: E402

USER = ("testuser01@example.com", "Test@1234")
OTHER = ("other@example.com", "Other@1234")
ADMIN = ("admin01@example.com", "Admin@1234")
# Java quiz answers: correct options are B, C, C, B, B
CORRECT = {1: "B", 2: "C", 3: "C", 4: "B", 5: "B"}


def build_db(path):
    con = sqlite3.connect(path)
    with open(os.path.join(APP_DIR, "schema.sql")) as f:
        con.executescript(f.read())
    users = [("testuser01", USER, "User"), ("other", OTHER, "User"), ("admin01", ADMIN, "Administrator")]
    for name, (email, pw), role in users:
        con.execute("INSERT INTO User(name,email,password,role) VALUES (?,?,?,?)",
                    (name, email, generate_password_hash(pw, method="pbkdf2:sha256"), role))
    con.execute("INSERT INTO Category(name,description) VALUES ('Java','Core Java')")
    con.execute("INSERT INTO Category(name,description) VALUES ('Python','Python basics')")
    con.execute("INSERT INTO Quiz(title,time_limit,category_id,created_by) VALUES ('Java Basics Quiz',10,1,3)")
    con.execute("INSERT INTO Quiz(title,time_limit,category_id,created_by) VALUES ('Empty Quiz',5,2,3)")
    qs = [("Inherit keyword?", "this", "extends", "implements", "super", "B"),
          ("Not primitive?", "int", "boolean", "String", "char", "C"),
          ("Entry point?", "start()", "run()", "main()", "init()", "C"),
          ("No duplicates?", "List", "Set", "ArrayList", "Vector", "B"),
          ("Prevents subclassing?", "static", "final", "abstract", "private", "B")]
    con.executemany("INSERT INTO Question(quiz_id,question_text,option_a,option_b,option_c,option_d,correct_option)"
                    " VALUES (1,?,?,?,?,?,?)", qs)
    con.commit()
    con.close()


@pytest.fixture
def db_path(tmp_path, monkeypatch):
    path = str(tmp_path / "test_quiz.db")
    build_db(path)
    monkeypatch.setattr(quiz_app, "DB", path)
    quiz_app.app.config["TESTING"] = True
    return path


@pytest.fixture
def client(db_path):
    with quiz_app.app.test_client() as c:
        yield c


@pytest.fixture
def make_client(db_path):
    """Create extra independent browser sessions (another user, an admin)."""
    return lambda: quiz_app.app.test_client()


def scalar(path, sql, *args):
    """Run one query against the test database and return the first value."""
    con = sqlite3.connect(path)
    try:
        return con.execute(sql, args).fetchone()[0]
    finally:
        con.close()


def execute(path, sql, *args):
    con = sqlite3.connect(path)
    try:
        con.execute(sql, args)
        con.commit()
    finally:
        con.close()


def table_rows(page):
    """Only the table body, so the 'Hi, <name>' header does not interfere."""
    return page[page.index(b"<tbody"):]


def login(c, creds):
    return c.post("/login", data={"email": creds[0], "password": creds[1]})


def start_quiz(c, quiz_id=1, seconds_ago=None):
    c.get(f"/quiz/{quiz_id}")
    if seconds_ago is not None:
        import time
        with c.session_transaction() as s:
            s[f"quiz_started_at_{quiz_id}"] = time.time() - seconds_ago


def submit(c, answers, quiz_id=1, timeout=False):
    data = {f"q_{k}": v for k, v in answers.items()}
    if timeout:
        data["timeout_submission"] = "1"
    return c.post(f"/quiz/{quiz_id}/submit", data=data)
