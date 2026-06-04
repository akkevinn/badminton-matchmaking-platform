"""Vercel serverless entrypoint.

Vercel's Python runtime serves the `app` ASGI application exported here.
We add the repo root to sys.path so `backend` imports resolve, then expose
the existing FastAPI app unchanged.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.main import app  # noqa: E402

# `app` is what Vercel's @vercel/python runtime looks for.
