"""Flask application factory for CodeCraftHub."""
from __future__ import annotations

import os

from flask import Flask, jsonify, send_from_directory

from .routes import bp as courses_bp

WEB_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web"
)


def create_app() -> Flask:
    app = Flask(__name__, static_folder=None)

    # All course endpoints are served under /api (e.g. /api/courses).
    app.register_blueprint(courses_bp, url_prefix="/api")

    # Serve the single-page frontend at the root URL.
    @app.get("/")
    def index():
        return send_from_directory(WEB_DIR, "index.html")

    # Permissive CORS so the HTML file also works when opened directly
    # (e.g. via file://) or from a different origin.
    @app.after_request
    def _cors(resp):
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Methods"] = (
            "GET,POST,PUT,PATCH,DELETE,OPTIONS"
        )
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return resp

    # Handle CORS preflight for any /api/* path.
    @app.route("/api/<path:_any>", methods=["OPTIONS"])
    def _preflight(_any):
        return ("", 204)

    @app.errorhandler(404)
    def _not_found(_e):
        return jsonify({"error": "Not found."}), 404

    @app.errorhandler(405)
    def _method_not_allowed(_e):
        return jsonify({"error": "Method not allowed."}), 405

    return app
