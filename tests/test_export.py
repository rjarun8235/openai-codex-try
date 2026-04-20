from io import BytesIO

from PIL import Image

from app import create_app


def _grid(color="#112233"):
    return [[color for _ in range(32)] for _ in range(32)]


def _client():
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        }
    )
    return app.test_client()


def test_export_returns_png():
    client = _client()

    response = client.post(
        "/export",
        json={
            "name": "Sunset Draft",
            "pixel_data": _grid(),
        },
    )

    assert response.status_code == 200
    assert response.mimetype == "image/png"
    assert "sunset-draft.png" in response.headers["Content-Disposition"]

    image = Image.open(BytesIO(response.data))
    assert image.format == "PNG"
    assert image.size == (512, 512)
    assert image.getpixel((0, 0)) == (17, 34, 51)


def test_export_rejects_invalid_input():
    client = _client()

    response = client.post(
        "/export",
        json={
            "name": "",
            "pixel_data": _grid(),
        },
    )

    assert response.status_code == 400
    assert response.get_json() == {
        "ok": False,
        "message": "Please enter a canvas name.",
    }
