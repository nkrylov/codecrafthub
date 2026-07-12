"""Flask application factory for CodeCraftHub."""
from __future__ import annotations

from flask import Flask, jsonify

from .routes import bp as courses_bp


def create_app() -> Flask:
    app = Flask(__name__)

    # All course endpoints are served under /api (e.g. /api/courses).
    app.register_blueprint(courses_bp, url_prefix="/api")

    @app.errorhandler(404)
    def _not_found(_e):
        return jsonify({"error": "Not found."}), 404

    @app.errorhandler(405)
    def _method_not_allowed(_e):
        return jsonify({"error": "Method not allowed."}), 405

    return app

