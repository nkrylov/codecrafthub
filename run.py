"""Entry point for running the CodeCraftHub development server."""
from __future__ import annotations

import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    # debug=False keeps the test script deterministic (no reloader spawning
    # a second process that would break our PID tracking).
    app.run(host="127.0.0.1", port=port, debug=False)

