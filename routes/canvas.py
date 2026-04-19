from flask import Blueprint, abort, jsonify, render_template, request, send_file

from services.canvas_service import (
    create_canvas,
    export_canvas_png,
    get_all_canvases,
    get_canvas_by_id,
)


canvas_bp = Blueprint("canvas", __name__)


@canvas_bp.get("/")
def index():
    return render_template("index.html")


@canvas_bp.get("/gallery")
def gallery():
    canvases = get_all_canvases()
    return render_template("gallery.html", canvases=canvases)


@canvas_bp.post("/canvases")
def save_canvas():
    payload = request.get_json(silent=True) or {}

    try:
        canvas = create_canvas(
            name=payload.get("name", ""),
            pixel_data=payload.get("pixel_data"),
        )
    except ValueError as exc:
        return jsonify({"ok": False, "message": str(exc)}), 400

    return (
        jsonify(
            {
                "ok": True,
                "message": f'Canvas "{canvas.name}" saved successfully.',
                "canvas": {
                    "id": canvas.id,
                    "name": canvas.name,
                    "created_at": canvas.created_at.isoformat(),
                },
            }
        ),
        201,
    )


@canvas_bp.get("/canvases/<int:canvas_id>/download")
def download_canvas(canvas_id):
    canvas = get_canvas_by_id(canvas_id)
    if canvas is None:
        abort(404)

    image_io, filename = export_canvas_png(canvas)
    return send_file(
        image_io,
        mimetype="image/png",
        as_attachment=True,
        download_name=filename,
    )
