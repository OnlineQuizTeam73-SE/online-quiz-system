"""Registration, login, logout and page protection (REQ-22, TC01-TC03, TC25)."""
import pytest
from conftest import scalar, USER, login

GOOD = {"name": "New", "email": "new@example.com", "password": "secret1", "confirm": "secret1"}


def test_register_success_then_login(client):
    r = client.post("/register", data=GOOD, follow_redirects=True)
    assert b"Registration successful" in r.data
    r = login(client, ("new@example.com", "secret1"))
    assert r.headers["Location"].endswith("/home")


@pytest.mark.parametrize("change, message", [
    ({"name": ""}, b"All fields are required"),
    ({"email": "not-an-email"}, b"valid email"),
    ({"password": "123", "confirm": "123"}, b"at least 6 characters"),
    ({"confirm": "different"}, b"do not match"),
    ({"email": "testuser01@example.com"}, b"already exists"),
    ({"name": "x" * 101}, b"at most 100 characters"),
])
def test_register_rejects_invalid_input(client, change, message):
    r = client.post("/register", data={**GOOD, **change})
    assert r.status_code == 200 and message in r.data


def test_register_page_loads(client):
    assert client.get("/register").status_code == 200


def test_password_is_stored_hashed(client, db_path):
    client.post("/register", data=GOOD)
    stored = scalar(db_path, "SELECT password FROM User WHERE email=?", "new@example.com")
    assert stored != "secret1" and stored.startswith("pbkdf2:sha256")


def test_login_wrong_password_rejected(client):
    r = login(client, (USER[0], "wrong"))
    assert r.status_code == 200 and b"Invalid email or password" in r.data


def test_login_page_loads(client):
    assert client.get("/login").status_code == 200


def test_index_redirects(client):
    assert client.get("/").status_code == 302


@pytest.mark.parametrize("url", ["/home", "/category/1", "/quiz/1", "/leaderboard", "/results/history", "/result/1"])
def test_protected_pages_need_login(client, url):
    r = client.get(url)
    assert r.status_code == 302 and "/login" in r.headers["Location"]


def test_logout_blocks_protected_pages(client):
    login(client, USER)
    assert client.get("/home").status_code == 200
    client.get("/logout")
    assert "/login" in client.get("/home").headers["Location"]
