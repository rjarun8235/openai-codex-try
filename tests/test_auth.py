from contextlib import contextmanager

import pytest
from flask import template_rendered

from app import create_app
from models import User, db
from services.auth_service import create_user_account


@pytest.fixture()
def app():
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret",
        }
    )

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@contextmanager
def _captured_templates(app):
    recorded = []

    def record(sender, template, context, **extra):
        recorded.append((template, context))

    template_rendered.connect(record, app)
    try:
        yield recorded
    finally:
        template_rendered.disconnect(record, app)


def _create_user(app, username="PainterOne", email="painter@example.com", password="password123"):
    with app.app_context():
        return create_user_account(username=username, email=email, password=password)


def test_auth_pages_render_for_anonymous_user(client):
    signup_response = client.get("/auth/signup")
    login_response = client.get("/auth/login")
    with _captured_templates(client.application) as templates:
        index_response = client.get("/")

    assert signup_response.status_code == 200
    assert b"<h1>Create account</h1>" in signup_response.data
    assert b'action="/auth/signup"' in signup_response.data

    assert login_response.status_code == 200
    assert b"<h1>Log in</h1>" in login_response.data
    assert b'action="/auth/login"' in login_response.data

    assert index_response.status_code == 200
    assert b"Create account" in index_response.data
    assert b"Signed in as" not in index_response.data
    assert templates[-1][1]["current_user"] is None
    assert templates[-1][1]["is_authenticated"] is False


def test_signup_json_creates_account_session_and_authenticated_context(client, app):
    response = client.post(
        "/auth/signup",
        json={
            "username": "Painter_01",
            "email": "Painter@Example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 201
    assert response.get_json()["ok"] is True
    assert response.get_json()["message"] == "Account created successfully."
    assert response.get_json()["user"]["username"] == "Painter_01"
    assert response.get_json()["user"]["email"] == "painter@example.com"

    with client.session_transaction() as session_state:
        assert session_state["user_id"]

    session_response = client.get("/auth/session")
    assert session_response.get_json()["authenticated"] is True
    assert session_response.get_json()["user"]["username"] == "Painter_01"

    with _captured_templates(client.application) as templates:
        index_response = client.get("/")

    assert index_response.status_code == 200
    assert templates[-1][1]["current_user"].username == "Painter_01"
    assert templates[-1][1]["is_authenticated"] is True

    redirect_response = client.get("/auth/signup")
    assert redirect_response.status_code == 302
    assert redirect_response.headers["Location"].endswith("/")

    with app.app_context():
        assert db.session.scalar(db.select(db.func.count(User.id))) == 1


def test_signup_form_rejects_duplicate_username(client, app):
    _create_user(app, username="PainterOne", email="existing@example.com")

    response = client.post(
        "/auth/signup",
        data={
            "username": "PainterOne",
            "email": "new@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 400
    assert b"<h1>Create account</h1>" in response.data
    assert b"That username is already taken." in response.data

    session_response = client.get("/auth/session")
    assert session_response.get_json() == {
        "ok": True,
        "authenticated": False,
        "user": None,
    }


def test_login_form_redirects_and_authenticates_existing_user(client, app):
    _create_user(app, username="PainterOne", email="painter@example.com", password="password123")

    response = client.post(
        "/auth/login",
        data={
            "identifier": "painterone",
            "password": "password123",
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")

    session_response = client.get("/auth/session")
    assert session_response.get_json()["authenticated"] is True
    assert session_response.get_json()["user"]["email"] == "painter@example.com"

    with _captured_templates(client.application) as templates:
        index_response = client.get("/")

    assert index_response.status_code == 200
    assert templates[-1][1]["current_user"].username == "PainterOne"
    assert templates[-1][1]["is_authenticated"] is True

    redirect_response = client.get("/auth/login")
    assert redirect_response.status_code == 302
    assert redirect_response.headers["Location"].endswith("/")


def test_login_json_rejects_invalid_password(client, app):
    _create_user(app, username="PainterOne", email="painter@example.com", password="password123")

    response = client.post(
        "/auth/login",
        json={
            "identifier": "painter@example.com",
            "password": "wrongpass",
        },
    )

    assert response.status_code == 401
    assert response.get_json() == {
        "ok": False,
        "message": "Invalid username/email or password.",
    }

    session_response = client.get("/auth/session")
    assert session_response.get_json()["authenticated"] is False


def test_logout_json_clears_session_and_restores_anonymous_context(client):
    client.post(
        "/auth/signup",
        json={
            "username": "Painter_01",
            "email": "Painter@Example.com",
            "password": "password123",
        },
    )

    response = client.post("/auth/logout", json={})

    assert response.status_code == 200
    assert response.get_json() == {
        "ok": True,
        "message": "Logged out successfully.",
    }

    with client.session_transaction() as session_state:
        assert "user_id" not in session_state

    session_response = client.get("/auth/session")
    assert session_response.get_json() == {
        "ok": True,
        "authenticated": False,
        "user": None,
    }

    index_response = client.get("/")
    assert b"Create account" in index_response.data
    assert b"Signed in as" not in index_response.data


def test_logout_form_redirects_when_no_user_is_signed_in(client):
    response = client.post("/auth/logout", data={})

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")

    session_response = client.get("/auth/session")
    assert session_response.get_json()["authenticated"] is False
