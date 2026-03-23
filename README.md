# HawkEar Analysis

A full-stack application for analysing the striking accuracy of bell-ringing performances. Upload a method file and one or more timing recordings, then explore visualisations showing striking errors, tempo changes, method mistakes, and individual ringer characteristics.

---

## Prerequisites

| Tool | Minimum version |
|------|----------------|
| Python | 3.11 |
| Node.js | 18 |
| npm | 9 |

---

## Running locally

### 1. Clone and enter the repo

```bash
git clone https://github.com/KateR-S/hawkear-analysis.git
cd hawkear-analysis
```

### 2. Set up the backend

```bash
cd backend

# Create and activate a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `dev-secret-key-change-in-production` | JWT signing secret — **change this for anything beyond local dev** |
| `DATABASE_URL` | `sqlite:///./hawkear.db` (inside `backend/`) | SQLAlchemy database URL |

You can set these in your shell or create a `.env` file (not committed).

```bash
export SECRET_KEY="a-long-random-string"
```

#### Start the API server

```bash
# From the backend/ directory, with the venv active
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
# OR run from the repo root:
cd ..
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

The API will be available at <http://localhost:8000>. Interactive docs are at <http://localhost:8000/docs>.

### 3. Set up the frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

The development server starts at <http://localhost:5173>. It proxies all `/api` requests to the backend on port 8000, so both processes must be running.

### 4. Open the app

Visit <http://localhost:5173> in your browser. Register an account, then:

1. Create a **Touch** and upload its method (`.txt`) file.
2. Upload one or more timing (`.csv`) files as **Performances** and drag them into the order you want.
3. Go to **Analysis** to view striking accuracy, tempo, method mistakes, and ringer characteristics.

---

## Running the tests

```bash
cd backend
python -m pytest tests/ -v
```

All tests use an in-memory SQLite database and synthetic data — no example files are required.

---

## Example data files

The `examples/` directory contains a real 12-bell touch recorded at Taunton:

| File | Description |
|------|-------------|
| `Taunton.20260322-1210.Touch1.uzcu.rf.txt` | Expected row-by-row bell order (method file) |
| `Taunton.20260322-1210.Touch1.uzcu.bl.csv` | Actual strike times in milliseconds (timing file) |

You can upload these through the UI to try the analysis immediately after starting the app.

### File formats

**Method file (`.txt`)** — one row per line, each character is a bell:
- `1`–`9` = bells 1–9
- `0` = bell 10
- `E` = bell 11
- `T` = bell 12

```
1234567890ET   ← rounds (bells in order)
213547698E0T   ← first change row
...
```

**Timing file (`.csv`)** — two columns, one strike per line:

```
Bell No,Actual Time
1,18340
2,18650
3,18950
...
```

---

## Training ringer characteristics

Drop zip archives containing a method `.txt` and one or more timing `.csv` files into the `training_data/` directory. Each zip should represent a single touch. Use the **Training** page in the app to trigger retraining and provide feedback on whether detected characteristics are useful.

---

## Project structure

```
hawkear-analysis/
├── backend/
│   ├── main.py              # FastAPI app entry point
│   ├── database.py          # SQLAlchemy engine & session
│   ├── models.py            # ORM models
│   ├── schemas.py           # Pydantic schemas
│   ├── auth.py              # JWT helpers
│   ├── routers/             # API route handlers
│   │   ├── auth.py
│   │   ├── touches.py
│   │   ├── performances.py
│   │   └── analysis.py
│   ├── services/            # Business logic
│   │   ├── parser.py        # Method & timing file parsers
│   │   ├── analysis.py      # Striking accuracy engine
│   │   └── characteristics.py  # Ringer characteristics
│   ├── tests/               # pytest test suite
│   └── requirements.txt
├── frontend/                # React + TypeScript + Vite
│   ├── src/
│   │   ├── api/             # Typed API client
│   │   ├── components/      # Shared UI components & charts
│   │   ├── contexts/        # Auth context
│   │   ├── pages/           # Route-level page components
│   │   └── types/           # TypeScript type definitions
│   └── package.json
├── examples/                # Example method and timing files
├── training_data/           # Drop zips here for characteristics training
├── railway.toml             # Railway deployment config
└── Procfile
```

---

## Deployment (Railway)

The app is configured for [Railway](https://railway.app) via `railway.toml`. A single service builds the frontend and serves it as static files from the FastAPI backend.

Set the following environment variables in your Railway service settings:

| Variable | Notes |
|----------|-------|
| `SECRET_KEY` | Any long random string |
| `DATABASE_URL` | Leave unset to use SQLite, or set a PostgreSQL URL for persistence |
| `PORT` | Set automatically by Railway |
