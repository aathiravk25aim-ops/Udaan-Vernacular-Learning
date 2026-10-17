"""Packaged entry point for the Udaan local API server."""
from __future__ import annotations

import os
import uvicorn
from app import app


if __name__ == "__main__":
    # The desktop shell probes this address before opening the window.
    # Keep the server in the foreground so Electron can supervise its lifetime.
    uvicorn.run(
        app,
        host=os.environ.get("UDAAN_HOST", "127.0.0.1"),
        port=int(os.environ.get("UDAAN_PORT", "8765")),
        log_level=os.environ.get("UDAAN_LOG_LEVEL", "info"),
        access_log=True,
    )
