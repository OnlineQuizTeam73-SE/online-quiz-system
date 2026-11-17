"""Categories, quiz flow, timer and scoring (REQ-01 to REQ-13, TC05-TC12, TC17)."""
from conftest import scalar, CORRECT, USER, login, start_quiz, submit


def test_home_lists_categories(client):
    login(client, USER)
    r = client.get("/home")
    assert b"Java" in r.data and b"Python" in r.data


def test_category_lists_its_quizzes(client):
    login(client, USER)
    r = client.get("/category/1")
    assert b"Java Basics Quiz" in r.data and b"Empty Quiz" not in r.data


def test_unknown_category_redirects(client):
    login(client, USER)
    assert client.get("/category/99").headers["Location"].endswith("/home")


def test_quiz_page_shows_questions_without_answers(client):
    login(client, USER)
    r = client.get("/quiz/1")
    assert b"Inherit keyword?" in r.data and b"correct_option" not in r.data


def test_unknown_quiz_redirects(client):
    login(client, USER)
    assert client.get("/quiz/99").headers["Location"].endswith("/home")
    assert client.post("/quiz/99/submit").headers["Location"].endswith("/home")


def test_all_correct_scores_full_marks(client, db_path):
    login(client, USER)
    start_quiz(client)
    r = submit(client, CORRECT)
    assert "/result/" in r.headers["Location"]
    assert scalar(db_path, "SELECT score FROM Result") == 5


def test_partial_and_unanswered_scoring(client, db_path):
    login(client, USER)
    start_quiz(client)
    submit(client, {1: "B", 2: "A", 3: "z"})  # 1 right, 1 wrong, 1 invalid, 2 blank
    assert scalar(db_path, "SELECT score FROM Result") == 1


def test_duplicate_submission_is_refused(client, db_path):
    login(client, USER)
    start_quiz(client)
    submit(client, CORRECT)
    r = submit(client, CORRECT)
    assert "/category/1" in r.headers["Location"]
    assert scalar(db_path, "SELECT COUNT(*) FROM Result") == 1


def test_submit_without_starting_is_refused(client):
    login(client, USER)
    r = submit(client, CORRECT, )
    assert "/category/" in r.headers["Location"]


def test_late_manual_submission_rejected(client, db_path):
    login(client, USER)
    start_quiz(client, seconds_ago=10 * 60 + 2)
    r = submit(client, CORRECT)
    assert "/category/1" in r.headers["Location"]
    assert scalar(db_path, "SELECT COUNT(*) FROM Result") == 0


def test_auto_submit_inside_grace_period_accepted(client):
    login(client, USER)
    start_quiz(client, seconds_ago=10 * 60 + 3)
    assert "/result/" in submit(client, CORRECT, timeout=True).headers["Location"]


def test_auto_submit_after_grace_period_rejected(client):
    login(client, USER)
    start_quiz(client, seconds_ago=10 * 60 + 6)
    assert "/category/1" in submit(client, CORRECT, timeout=True).headers["Location"]


def test_time_taken_is_capped_at_limit(client, db_path):
    login(client, USER)
    start_quiz(client, seconds_ago=10 * 60 + 3)
    submit(client, CORRECT, timeout=True)
    assert scalar(db_path, "SELECT time_taken FROM Result") == 600


def test_quiz_without_questions_is_refused(client):
    login(client, USER)
    start_quiz(client, quiz_id=2)
    r = submit(client, {}, quiz_id=2)
    assert "/category/2" in r.headers["Location"]


def test_refreshing_quiz_page_does_not_restart_timer(client):
    login(client, USER)
    client.get("/quiz/1")
    with client.session_transaction() as s:
        started = s["quiz_started_at_1"]
    client.get("/quiz/1")
    with client.session_transaction() as s:
        assert s["quiz_started_at_1"] == started
