import io
import re

from PIL import Image
from models import Canvas, db


GRID_SIZE = 32
HEX_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
FILENAME_SAFE_RE = re.compile(r"[^A-Za-z0-9_-]+")


def _validate_name(name):
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Please enter a canvas name.")

    cleaned_name = name.strip()
    if len(cleaned_name) > 255:
        raise ValueError("Canvas name must be 255 characters or fewer.")

    return cleaned_name


def _validate_pixel_data(pixel_data):
    if not isinstance(pixel_data, list) or len(pixel_data) != GRID_SIZE:
        raise ValueError("Pixel data must be a 32x32 grid.")

    validated_rows = []

    for row in pixel_data:
        if not isinstance(row, list) or len(row) != GRID_SIZE:
            raise ValueError("Pixel data must be a 32x32 grid.")

        validated_row = []
        for color in row:
            if not isinstance(color, str) or not HEX_COLOR_RE.fullmatch(color):
                raise ValueError("Each pixel must be a hex color like #FFFFFF.")
            validated_row.append(color.upper())

        validated_rows.append(validated_row)

    return validated_rows


def create_canvas(name, pixel_data):
    canvas = Canvas(
        name=_validate_name(name),
        pixel_data=_validate_pixel_data(pixel_data),
    )
    db.session.add(canvas)
    db.session.commit()
    return canvas


def get_all_canvases():
    return Canvas.query.order_by(Canvas.created_at.desc()).all()


def get_canvas_by_id(canvas_id):
    return db.session.get(Canvas, canvas_id)


def _sanitize_filename(name):
    normalized = FILENAME_SAFE_RE.sub("-", name.strip().lower()).strip("-")
    if not normalized:
        normalized = "pixel-art-canvas"
    return normalized


def export_canvas_png(canvas, pixel_size=16):
    validated_rows = _validate_pixel_data(canvas.pixel_data)
    image_size = GRID_SIZE * pixel_size
    image = Image.new("RGB", (image_size, image_size), color="#FFFFFF")

    for row_index, row in enumerate(validated_rows):
        for col_index, color in enumerate(row):
            x0 = col_index * pixel_size
            y0 = row_index * pixel_size

            for y in range(y0, y0 + pixel_size):
                for x in range(x0, x0 + pixel_size):
                    image.putpixel((x, y), color)

    image_io = io.BytesIO()
    image.save(image_io, format="PNG")
    image_io.seek(0)

    filename = f"{_sanitize_filename(canvas.name)}.png"
    return image_io, filename
