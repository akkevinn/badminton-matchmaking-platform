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

## Deploy on GCP Spot VM

### Prerequisites
- Docker and Docker Compose installed on the VM
- Port 8000 open in the VM's firewall rules

### Steps
```bash
# 1. Copy the project to the VM (from your local machine)
gzip -c badminton-matchmaking-platform | ssh user@VM_IP 'cat | tar -xz'

# 2. SSH into the VM
ssh user@VM_IP

# 3. Start the container
cd badminton-matchmaking-platform
docker compose up -d
```

Access the app at **http://VM_EXTERNAL_IP:8000**

### Useful Docker commands
```bash
docker compose logs -f        # live logs
docker compose restart        # restart after a code change
docker compose down           # stop
docker compose down -v        # stop and delete the database volume
```

The database is stored in a Docker volume (`badminton_data`) and survives container restarts.

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
| Backend  | Python · FastAPI · SQLite (SQLAlchemy) |
| Frontend | Vanilla HTML / CSS / JavaScript |
| Images   | Pillow (Instagram story generator) |
| Deploy   | Docker · docker-compose |

---

## Scoring System
| Event | Points |
|-------|--------|
| Win   | 3 pts  |
| Loss  | 1 pt (participation) |
| Compensation | `avg_pts_per_game × (max_games − your_games)` |

Final rank = **total points** (raw + compensation) descending.
Compensation ensures players who joined late or left early are not unfairly penalised.
