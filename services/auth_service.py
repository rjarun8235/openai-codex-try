import re

from flask import g, session
from werkzeug.security import check_password_hash, generate_password_hash

from models import User, db


USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,32}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class AuthenticationError(ValueError):
    pass


def _normalize_username(username):
    if not isinstance(username, str):
        raise ValueError("Username is required.")

    normalized_username = username.strip()
    if not normalized_username:
        raise ValueError("Username is required.")
    if not USERNAME_RE.fullmatch(normalized_username):
        raise ValueError(
            "Username must be 3-32 characters and use only letters, numbers, or underscores."
        )

    return normalized_username


def _normalize_email(email):
    if not isinstance(email, str):
        raise ValueError("Email is required.")

    normalized_email = email.strip().lower()
    if not normalized_email:
        raise ValueError("Email is required.")
    if len(normalized_email) > 255:
        raise ValueError("Email must be 255 characters or fewer.")
    if not EMAIL_RE.fullmatch(normalized_email):
        raise ValueError("Please enter a valid email address.")

    return normalized_email


def _validate_password(password):
    if not isinstance(password, str):
        raise ValueError("Password is required.")
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters.")
    if len(password) > 255:
        raise ValueError("Password must be 255 characters or fewer.")

    return password


def serialize_user(user):
    if user is None:
        return None

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "created_at": user.created_at.isoformat(),
    }


def create_user_account(username, email, password):
    normalized_username = _normalize_username(username)
    normalized_email = _normalize_email(email)
    validated_password = _validate_password(password)
    username_key = normalized_username.lower()

    existing_user = User.query.filter(
        (User.username_key == username_key) | (User.email == normalized_email)
    ).first()
    if existing_user is not None:
        if existing_user.username_key == username_key:
            raise ValueError("That username is already taken.")
        raise ValueError("That email is already registered.")

    user = User(
        username=normalized_username,
        username_key=username_key,
        email=normalized_email,
        password_hash=generate_password_hash(validated_password),
    )
    db.session.add(user)
    db.session.commit()
    return user


def authenticate_user(identifier, password):
    validated_password = _validate_password(password)

    if not isinstance(identifier, str) or not identifier.strip():
        raise ValueError("Username or email is required.")

    normalized_identifier = identifier.strip().lower()
    user = User.query.filter(
        (User.username_key == normalized_identifier) | (User.email == normalized_identifier)
    ).first()

    if user is None or not check_password_hash(user.password_hash, validated_password):
        raise AuthenticationError("Invalid username/email or password.")

    return user


def login_user(user):
    session.clear()
    session["user_id"] = user.id


def logout_user():
    session.clear()


def load_current_user():
    user_id = session.get("user_id")
    if user_id is None:
        g.current_user = None
        return None

    user = db.session.get(User, user_id)
    if user is None:
        session.clear()
        g.current_user = None
        return None

    g.current_user = user
    return user


def get_current_user():
    if hasattr(g, "current_user"):
        return g.current_user
    return load_current_user()
