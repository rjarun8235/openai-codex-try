from flask import Blueprint, jsonify, request, send_file

from services.export_service import export_canvas_payload


export_bp = Blueprint("export", __name__, url_prefix="/export")


@export_bp.post("")
def export_canvas():
    payload = request.get_json(silent=True) or {}

    try:
        image_io, filename = export_canvas_payload(
            name=payload.get("name", ""),
            pixel_data=payload.get("pixel_data"),
        )
    except ValueError as exc:
        return jsonify({"ok": False, "message": str(exc)}), 400

    return send_file(
        image_io,
        mimetype="image/png",
        as_attachment=True,
        download_name=filename,
    )
