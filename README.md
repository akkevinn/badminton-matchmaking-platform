# Badminton Matchmaking Platform
**Prunus Sport** — skill-balanced badminton tournament manager.

---

## Run Locally

### First time / one-liner
```bash
cd badminton-matchmaking-platform
chmod +x run.sh
./run.sh
```
The script auto-creates a Python virtual environment, installs dependencies, and starts the server.

Open **http://localhost:8000** in your browser.

### Subsequent runs
```bash
./run.sh
```
That's it. The database (`badminton.db`) is kept in the project folder and persists between runs.

### Stop the server
Press `Ctrl + C` in the terminal.

### Kill a leftover server (if port 8000 is busy)
```bash
lsof -ti :8000 | xargs kill -9
```

---

## Deploy free on Render + Turso

The app runs on **Render** (free web service, runs the `Dockerfile`) and stores
data in **Turso** (free hosted SQLite). No code changes are needed between local
and production — set two env vars and Turso takes over from the local file.

### 1. Create the Turso database
Install the CLI (`brew install tursodatabase/tap/turso`), then:
```bash
turso auth signup                       # or: turso auth login
turso db create badminton               # create the database
turso db show badminton --url           # -> libsql://badminton-<org>.turso.io  (TURSO_DATABASE_URL)
turso db tokens create badminton        # -> a long token              (TURSO_AUTH_TOKEN)
```

### 2. Deploy on Render
1. Push this repo to GitHub (already done).
2. On [render.com](https://render.com): **New → Blueprint**, pick this repo. Render
   reads `render.yaml` and provisions a free Docker web service.
3. In the service's **Environment** tab, set the two secrets from step 1:
   - `TURSO_DATABASE_URL`
   - `TURSO_AUTH_TOKEN`
4. Deploy. Render builds the `Dockerfile` and gives you a public
   `https://badminton-matchmaking.onrender.com` URL.

Tables are created automatically on first startup (`init_db()`).

> **Note:** Render's free tier sleeps the service after ~15 min of inactivity, so
> the first request after idle takes ~30–50s to wake. Data lives in Turso, so it
> persists across sleeps, restarts, and redeploys.

---

## Project Structure
```
badminton-matchmaking-platform/
├── backend/
│   ├── main.py               # FastAPI app entry point
│   ├── models.py             # Database models
│   ├── schemas.py            # Request/response shapes
│   ├── database.py           # SQLite connection
│   ├── routers/              # API route handlers
│   │   ├── players.py
│   │   ├── tournaments.py
│   │   ├── matches.py
│   │   └── story.py
│   └── services/
│       ├── matchmaking.py    # Skill-balanced match generation
│       ├── leaderboard.py    # Points & compensation calculation
│       └── instagram.py      # Instagram story image generator
├── frontend/                 # Plain HTML/CSS/JS (no build step)
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── app.js
│       ├── api.js
│       └── utils.js
├── assets/
│   └── prunus-sport.png      # Brand logo
├── run.sh                    # Local start script
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## Tech Stack
| Layer    | Technology |
|----------|-----------|
| Backend  | Python · FastAPI · SQLite / Turso (SQLAlchemy) |
| Frontend | Vanilla HTML / CSS / JavaScript |
| Images   | Pillow (Instagram story generator) |
| Deploy   | Docker · Render (compute) · Turso (database) |

---

## Scoring System
| Event | Points |
|-------|--------|
| Win   | 3 pts  |
| Loss  | 1 pt (participation) |
| Compensation | `avg_pts_per_game × (max_games − your_games)` |

Final rank = **total points** (raw + compensation) descending.
Compensation ensures players who joined late or left early are not unfairly penalised.
