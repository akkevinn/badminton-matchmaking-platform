from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
import os

from backend.database import init_db
from backend.routers import players, tournaments, matches, story

app = FastAPI(title="Badminton Matchmaking", version="1.0.0")

# Init DB on startup
@app.on_event("startup")
def startup():
    init_db()


# API routes
app.include_router(players.router)
app.include_router(tournaments.router)
app.include_router(matches.router)
app.include_router(story.router)

# Serve assets (logo etc.)
ASSETS_DIR = Path(__file__).parent.parent / "assets"
app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")

# Serve frontend
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/{full_path:path}")
def serve_frontend(full_path: str):
    index = FRONTEND_DIR / "index.html"
    return FileResponse(str(index))
