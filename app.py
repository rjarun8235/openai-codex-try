import os
from pathlib import Path

from flask import Flask

from models import db
from routes.auth import auth_bp
from routes.canvas import canvas_bp
from routes.export import export_bp
from routes.health import health_bp
from services.auth_service import get_current_user, load_current_user


BASE_DIR = Path(__file__).resolve().parent


def create_app(test_config=None):
    app = Flask(__name__)

    env_secret = os.environ.get("PIXEL_ART_SECRET_KEY")
    if env_secret:
        app.config["SECRET_KEY"] = env_secret
    elif test_config is not None:
        app.config["SECRET_KEY"] = os.urandom(32).hex()
    else:
        raise RuntimeError("PIXEL_ART_SECRET_KEY must be set")

    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{BASE_DIR / 'pixel_art.db'}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    if test_config:
        app.config.update(test_config)

    db.init_app(app)

    @app.before_request
    def load_auth_state():
        load_current_user()

    @app.context_processor
    def inject_auth_context():
        current_user = get_current_user()
        return {
            "current_user": current_user,
            "is_authenticated": current_user is not None,
        }

    app.register_blueprint(auth_bp)
    app.register_blueprint(canvas_bp)
    app.register_blueprint(export_bp)
    app.register_blueprint(health_bp)

    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", debug=True)
