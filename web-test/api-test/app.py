from __future__ import annotations

from pathlib import Path

from flask import Flask, render_template, send_from_directory


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATE_DIR = BASE_DIR / "templates"
API_DIR = STATIC_DIR / "api"


app = Flask(
    __name__,
    static_folder=str(STATIC_DIR),
    template_folder=str(TEMPLATE_DIR),
)


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/<path:filename>")
def api_asset(filename: str):
    return send_from_directory(API_DIR, filename)


if __name__ == "__main__":
    app.run(debug=True, port=5102)
