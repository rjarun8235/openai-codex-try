from types import SimpleNamespace

from services.canvas_service import export_canvas_png, _validate_name, _validate_pixel_data


def export_canvas_payload(name, pixel_data):
    canvas_like = SimpleNamespace(
        name=_validate_name(name),
        pixel_data=_validate_pixel_data(pixel_data),
    )
    return export_canvas_png(canvas_like)
