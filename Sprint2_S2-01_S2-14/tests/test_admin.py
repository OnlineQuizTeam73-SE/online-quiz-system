"""Administrator access and content management (REQ-16 to REQ-19, REQ-23, TC18-TC22)."""
import pytest
from conftest import ADMIN, USER, login, scalar

ADMIN_PAGES = ["/admin", "/admin/quiz/1/questions", "/admin/question/1/edit"]
VALID_Q = {"question_text": "New question?", "option_a": "a", "option_b": "b",
           "option_c": "c", "option_d": "d", "correct_option": "A"}


@pytest.mark.parametrize("url", ADMIN_PAGES)
def test_normal_user_is_blocked(client, url):
    login(client, USER)
    r = client.get(url, follow_redirects=True)
    assert b"Access denied" in r.data


@pytest.mark.parametrize("url", ADMIN_PAGES)
def test_guest_is_sent_to_login(client, url):
    assert "/login" in client.get(url).headers["Location"]


def test_normal_user_cannot_post_admin_actions(client, db_path):
    login(client, USER)
    client.post("/admin/question/1/delete")
    client.post("/admin/category/add", data={"name": "Hack"})
    assert scalar(db_path, "SELECT COUNT(*) FROM Question") == 5
    assert scalar(db_path, "SELECT COUNT(*) FROM Category WHERE name='Hack'") == 0


@pytest.fixture
def admin(client):
    login(client, ADMIN)
    return client


def test_admin_dashboard_lists_quizzes(admin):
    r = admin.get("/admin")
    assert r.status_code == 200 and b"Java Basics Quiz" in r.data


def test_add_category(admin, db_path):
    r = admin.post("/admin/category/add", data={"name": "DBMS", "description": "x"}, follow_redirects=True)
    assert b"created successfully" in r.data
    assert scalar(db_path, "SELECT COUNT(*) FROM Category WHERE name='DBMS'") == 1


@pytest.mark.parametrize("name, message", [("", b"name is required"), ("Java", b"already exists")])
def test_add_category_rejects_bad_name(admin, name, message):
    assert message in admin.post("/admin/category/add", data={"name": name}, follow_redirects=True).data


def test_manage_questions_page(admin):
    assert b"Inherit keyword?" in admin.get("/admin/quiz/1/questions").data
    assert admin.get("/admin/quiz/99/questions").status_code == 302


def test_add_valid_question(admin, db_path):
    r = admin.post("/admin/quiz/1/question/add", data=VALID_Q, follow_redirects=True)
    assert b"Question added successfully" in r.data
    assert scalar(db_path, "SELECT COUNT(*) FROM Question") == 6


@pytest.mark.parametrize("change, message", [
    ({"option_c": ""}, b"are required"),
    ({"correct_option": "E"}, b"must be one of A, B, C, or D"),
])
def test_add_question_rejects_invalid_data(admin, db_path, change, message):
    r = admin.post("/admin/quiz/1/question/add", data={**VALID_Q, **change}, follow_redirects=True)
    assert message in r.data
    assert scalar(db_path, "SELECT COUNT(*) FROM Question") == 5


def test_edit_question(admin, db_path):
    assert admin.get("/admin/question/1/edit").status_code == 200
    r = admin.post("/admin/question/1/edit", data={**VALID_Q, "question_text": "Edited?"}, follow_redirects=True)
    assert b"updated successfully" in r.data
    assert scalar(db_path, "SELECT question_text FROM Question WHERE question_id=1") == "Edited?"


def test_edit_question_rejects_invalid_data(admin):
    r = admin.post("/admin/question/1/edit", data={**VALID_Q, "correct_option": "Z"}, follow_redirects=True)
    assert b"Invalid data" in r.data


def test_edit_and_delete_unknown_question(admin):
    assert b"Question not found" in admin.get("/admin/question/99/edit", follow_redirects=True).data
    assert b"Question not found" in admin.post("/admin/question/99/delete", follow_redirects=True).data


def test_delete_question(admin, db_path):
    r = admin.post("/admin/question/1/delete", follow_redirects=True)
    assert b"deleted successfully" in r.data
    assert scalar(db_path, "SELECT COUNT(*) FROM Question") == 4
