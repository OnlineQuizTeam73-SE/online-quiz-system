"""Result storage, report, history and leaderboard (REQ-13 to REQ-15, TC13-TC17)."""
from conftest import ADMIN, CORRECT, OTHER, USER, execute, login, scalar, start_quiz, submit, table_rows


def take_quiz(c, answers=CORRECT):
    start_quiz(c)
    return submit(c, answers).headers["Location"]


def test_result_and_answers_are_stored(client, db_path):
    login(client, USER)
    take_quiz(client)
    assert scalar(db_path, "SELECT COUNT(*) FROM Result") == 1
    assert scalar(db_path, "SELECT COUNT(*) FROM ResultAnswer") == 5


def test_report_shows_review_and_survives_refresh_and_relogin(client, make_client):
    login(client, USER)
    url = take_quiz(client, {1: "B", 2: "A"})
    first, refreshed = client.get(url).data, client.get(url).data
    assert first.count(b"(Correct)") == 1 and first.count(b"(Wrong)") == 4
    assert refreshed == first
    again = make_client()
    login(again, USER)
    assert again.get(url).data.count(b"(Wrong)") == 4


def test_other_user_cannot_open_report(client, make_client):
    login(client, USER)
    url = take_quiz(client)
    other = make_client()
    login(other, OTHER)
    assert other.get(url).headers["Location"].endswith("/home")


def test_admin_can_open_any_report(client, make_client):
    login(client, USER)
    url = take_quiz(client)
    admin = make_client()
    login(admin, ADMIN)
    assert admin.get(url).status_code == 200


def test_unknown_report_redirects(client):
    login(client, USER)
    assert client.get("/result/999").headers["Location"].endswith("/home")


def test_history_lists_attempts(client):
    login(client, USER)
    take_quiz(client)
    r = client.get("/results/history")
    assert b"Java Basics Quiz" in r.data and b"5 / 5" in r.data


def test_history_empty_state(client):
    login(client, USER)
    assert b"not completed any quizzes" in client.get("/results/history").data


def add_result(db_path, user_id, score, time_taken, when):
    execute(db_path, "INSERT INTO Result(user_id,quiz_id,score,time_taken,attempted_on) VALUES (?,?,?,?,?)",
            user_id, 1, score, time_taken, when)


def test_leaderboard_orders_by_score_then_time_then_date(client, db_path):
    add_result(db_path, 1, 4, 300, "2026-10-01 10:00:00")   # testuser01: lower score
    add_result(db_path, 2, 5, 200, "2026-10-02 10:00:00")   # other: same score, slower
    add_result(db_path, 3, 5, 100, "2026-10-03 10:00:00")   # admin01: same score, faster
    login(client, USER)
    page = table_rows(client.get("/leaderboard").data)
    assert page.index(b"admin01") < page.index(b"other") < page.index(b"testuser01")


def test_leaderboard_tie_on_score_and_time_uses_earlier_attempt(client, db_path):
    add_result(db_path, 2, 5, 100, "2026-10-05 10:00:00")
    add_result(db_path, 1, 5, 100, "2026-10-04 10:00:00")
    login(client, USER)
    page = table_rows(client.get("/leaderboard").data)
    assert page.index(b"testuser01") < page.index(b"other")


def test_leaderboard_filter_by_quiz(client, db_path):
    add_result(db_path, 1, 3, 100, "2026-10-01 10:00:00")
    login(client, USER)
    assert b"testuser01" in table_rows(client.get("/leaderboard?quiz_id=1").data)
    assert b"testuser01" not in table_rows(client.get("/leaderboard?quiz_id=2").data)


def test_old_database_gets_answer_table(db_path):
    import app as quiz_app
    execute(db_path, "DROP TABLE ResultAnswer")
    quiz_app.ensure_schema()
    assert scalar(db_path, "SELECT COUNT(*) FROM sqlite_master WHERE name='ResultAnswer'") == 1
