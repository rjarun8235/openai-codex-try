from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for

from services.auth_service import (
    AuthenticationError,
    authenticate_user,
    create_user_account,
    get_current_user,
    login_user,
    logout_user,
    serialize_user,
)


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def _request_data():
    if request.is_json:
        return request.get_json(silent=True) or {}
    return request.form.to_dict()


def _wants_json_response():
    if request.is_json:
        return True

    best_match = request.accept_mimetypes.best_match(["application/json", "text/html"])
    return best_match == "application/json"


@auth_bp.get("/session")
def auth_session():
    user = get_current_user()
    return jsonify(
        {
            "ok": True,
            "authenticated": user is not None,
            "user": serialize_user(user),
        }
    )


@auth_bp.get("/signup")
def signup_page():
    if get_current_user() is not None:
        return redirect(url_for("canvas.index"))
    return render_template("signup.html")


@auth_bp.post("/signup")
def signup():
    payload = _request_data()

    try:
        user = create_user_account(
            username=payload.get("username", ""),
            email=payload.get("email", ""),
            password=payload.get("password", ""),
        )
    except ValueError as exc:
        if _wants_json_response():
            return jsonify({"ok": False, "message": str(exc)}), 400

        flash(str(exc), "error")
        return render_template("signup.html"), 400

    login_user(user)

    if _wants_json_response():
        return (
            jsonify(
                {
                    "ok": True,
                    "message": "Account created successfully.",
                    "user": serialize_user(user),
                }
            ),
            201,
        )

    flash("Account created successfully.", "success")
    return redirect(url_for("canvas.index"))


@auth_bp.get("/login")
def login_page():
    if get_current_user() is not None:
        return redirect(url_for("canvas.index"))
    return render_template("login.html")


@auth_bp.post("/login")
def login():
    payload = _request_data()

    try:
        user = authenticate_user(
            identifier=payload.get("identifier", ""),
            password=payload.get("password", ""),
        )
    except AuthenticationError as exc:
        if _wants_json_response():
            return jsonify({"ok": False, "message": str(exc)}), 401

        flash(str(exc), "error")
        return render_template("login.html"), 401
    except ValueError as exc:
        if _wants_json_response():
            return jsonify({"ok": False, "message": str(exc)}), 400

        flash(str(exc), "error")
        return render_template("login.html"), 400

    login_user(user)

    if _wants_json_response():
        return jsonify(
            {
                "ok": True,
                "message": "Logged in successfully.",
                "user": serialize_user(user),
            }
        )

    flash("Logged in successfully.", "success")
    return redirect(url_for("canvas.index"))


@auth_bp.post("/logout")
def logout():
    logout_user()

    if _wants_json_response():
        return jsonify({"ok": True, "message": "Logged out successfully."})

    flash("Logged out successfully.", "success")
    return redirect(url_for("canvas.index"))
