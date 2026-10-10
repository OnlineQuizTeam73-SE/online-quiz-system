"""S1-01: create the database and load the Test Plan sample data (section 14).
Run:  python init_db.py
"""
import os, sqlite3
from werkzeug.security import generate_password_hash

DB = os.path.join(os.path.dirname(__file__), "quiz.db")
if os.path.exists(DB):
    os.remove(DB)  # fresh start every time (dev only)

con = sqlite3.connect(DB)
con.execute("PRAGMA foreign_keys = ON")
with open(os.path.join(os.path.dirname(__file__), "schema.sql")) as f:
    con.executescript(f.read())

# Users (Test Plan: testuser01, admin01) -- passwords are for TESTING only
con.execute("INSERT INTO User(name,email,password,role) VALUES (?,?,?,?)",
            ("testuser01", "testuser01@example.com", generate_password_hash("Test@1234"), "User"))
con.execute("INSERT INTO User(name,email,password,role) VALUES (?,?,?,?)",
            ("admin01", "admin01@example.com", generate_password_hash("Admin@1234"), "Administrator"))
admin_id = con.execute("SELECT user_id FROM User WHERE name='admin01'").fetchone()[0]

# Categories (Test Plan: Java, DBMS, Python)
for n, d in [("Java", "Core Java concepts"), ("DBMS", "Database management systems"),
             ("Python", "Python programming basics")]:
    con.execute("INSERT INTO Category(name,description) VALUES (?,?)", (n, d))
java_id = con.execute("SELECT category_id FROM Category WHERE name='Java'").fetchone()[0]

# Quiz: Java Basics Quiz, 10 minutes
con.execute("INSERT INTO Quiz(title,time_limit,category_id,created_by) VALUES (?,?,?,?)",
            ("Java Basics Quiz", 10, java_id, admin_id))
quiz_id = con.execute("SELECT quiz_id FROM Quiz").fetchone()[0]

questions = [
    ("Which keyword is used to inherit a class in Java?", "this", "extends", "implements", "super", "B"),
    ("Which of these is NOT a primitive type in Java?", "int", "boolean", "String", "char", "C"),
    ("What is the entry point method of a Java program?", "start()", "run()", "main()", "init()", "C"),
    ("Which collection does not allow duplicate elements?", "List", "Set", "ArrayList", "Vector", "B"),
    ("Which keyword prevents a class from being subclassed?", "static", "final", "abstract", "private", "B"),
]
con.executemany("""INSERT INTO Question
    (quiz_id,question_text,option_a,option_b,option_c,option_d,correct_option)
    VALUES (?,?,?,?,?,?,?)""", [(quiz_id, *q) for q in questions])

con.commit()
for t in ("User", "Category", "Quiz", "Question", "Result"):
    print(f"{t}: {con.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]} rows")
con.close()
print("quiz.db created.")
