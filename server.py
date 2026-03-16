"""
Market Intelligence API server. Serves static frontend and JSON API.
Run from project root: python server.py
"""
from __future__ import annotations

import os
import sys

# Ensure src is on path for data imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from flask import Flask, send_from_directory

from routes import prices_bp, news_bp, map_bp, risk_bp, market_bp, misc_bp

app = Flask(__name__, static_folder="static", static_url_path="")
APP_ROOT = os.path.dirname(os.path.abspath(__file__))

app.register_blueprint(prices_bp)
app.register_blueprint(news_bp)
app.register_blueprint(map_bp)
app.register_blueprint(risk_bp)
app.register_blueprint(market_bp)
app.register_blueprint(misc_bp)


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(app.static_folder, path)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
