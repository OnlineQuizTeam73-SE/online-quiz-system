-- Team 73 Online Quiz System | S1-01 Database schema (per SRS Appendix B and ER diagram)
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS User (
    user_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name      VARCHAR(100) NOT NULL,
    email     VARCHAR(100) NOT NULL UNIQUE,
    password  VARCHAR(255) NOT NULL,              -- hashed, never plain text
    role      VARCHAR(20)  NOT NULL DEFAULT 'User'
              CHECK (role IN ('User', 'Administrator'))
);

CREATE TABLE IF NOT EXISTS Category (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name        VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(200)                       -- optional
);

CREATE TABLE IF NOT EXISTS Quiz (
    quiz_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    title       VARCHAR(100) NOT NULL,
    time_limit  INTEGER NOT NULL CHECK (time_limit > 0),   -- minutes
    category_id INTEGER NOT NULL,
    created_by  INTEGER NOT NULL,
    FOREIGN KEY (category_id) REFERENCES Category(category_id),
    FOREIGN KEY (created_by)  REFERENCES User(user_id)
);

CREATE TABLE IF NOT EXISTS Question (
    question_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    quiz_id        INTEGER NOT NULL,
    question_text  VARCHAR(500) NOT NULL,
    option_a       VARCHAR(200) NOT NULL,
    option_b       VARCHAR(200) NOT NULL,
    option_c       VARCHAR(200) NOT NULL,
    option_d       VARCHAR(200) NOT NULL,
    correct_option CHAR(1) NOT NULL CHECK (correct_option IN ('A','B','C','D')),
    FOREIGN KEY (quiz_id) REFERENCES Quiz(quiz_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Result (
    result_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL,
    quiz_id      INTEGER NOT NULL,
    score        INTEGER NOT NULL,
    time_taken   INTEGER NOT NULL,                 -- seconds
    attempted_on DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES User(user_id),
    FOREIGN KEY (quiz_id) REFERENCES Quiz(quiz_id)
);
