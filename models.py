from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

#adding reference comments


db = SQLAlchemy()


class Canvas(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    pixel_data = db.Column(db.JSON, nullable=False)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
