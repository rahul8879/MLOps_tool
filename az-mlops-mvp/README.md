# AstraZeneca MLOps MVP

---

## Project Structure

```
az-mlops-mvp/
├── README.md
├── backend/
│   ├── main.py                       ← FastAPI app + router registration
│   ├── requirements.txt              ← Pinned dependencies
│   ├── .env.example                  ← Env var template (copy → .env)
│   ├── Dockerfile
│   ├── core/
│   │   ├── config.py                 ← Pydantic BaseSettings (all env vars)
│   │   └── databricks_client.py      ← Singleton WorkspaceClient
│   ├── db/
│   │   ├── database.py               ← SQLAlchemy engine + session
│   │   ├── models.py                 ← ORM models (5 tables)
│   │   └── migrations/
│   │       └── init_schema.sql       ← Raw SQL reference schema
│   ├── schemas/
│   │   ├── experiment.py             ← Pydantic v2 experiment schemas
│   │   ├── run.py                    ← Pydantic v2 run schemas
│   │   └── submission.py             ← Pydantic v2 submission schemas
│   ├── routers/
│   │   ├── experiments.py            
│   │   ├── runs.py                   
│   │   └── submissions.py           
│   ├── services/
│   │   ├── experiment_service.py     ← Databricks SDK calls for experiments
│   │   ├── run_service.py            ← Databricks SDK calls for runs + comparison
│   │   └── submission_service.py     ← PostgreSQL persistence for submissions
│   └── tests/
│       ├── test_experiments.py
│       ├── test_runs.py
│       └── test_submissions.py
├── frontend/                         ← ??
└── notebooks/
    ├── 01_experiment_exploration.ipynb
    ├── 02_run_comparison.ipynb
    └── 03_schema_validation.ipynb
```

---

## Quick Start

### 1. Clone & navigate

```bash
git clone <your-repo-url>
cd az-mlops-mvp/backend
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your values:

```dotenv
DATABRICKS_HOST=https://adb-<workspace-id>.azuredatabricks.net
DATABRICKS_TOKEN=dapi_your_token_here
DATABASE_URL=postgresql+psycopg2://mlops_user:mlops_pass@localhost:5432/az_mlops
APP_ENV=development
```


### 5. Run the server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Visit:
- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

---

## Running with Docker

```bash
# Build
docker build -t az-mlops-backend .

# Run (pass env vars)
docker run -p 8000:8000 \
  -e DATABRICKS_HOST=https://your-workspace.azuredatabricks.net \
  -e DATABRICKS_TOKEN=dapi_your_token \
  -e DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/az_mlops \
  -e APP_ENV=production \
  az-mlops-backend
```

---

## Running Tests

```bash
cd backend

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --tb=short

# Run a specific test file
pytest tests/test_experiments.py -v
pytest tests/test_runs.py -v
pytest tests/test_submissions.py -v
```

---

## Database Migrations (Alembic)

```bash
# Initialise Alembic (first time only)
alembic init alembic

# Generate a new migration after model changes
alembic revision --autogenerate -m "describe your change"

# Apply all pending migrations
alembic upgrade head

# Roll back one migration
alembic downgrade -1
```

---

---

## Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| `DATABRICKS_HOST` | No* | Full workspace URL (enables live Databricks calls) |
| `DATABRICKS_TOKEN` | No* | PAT or Service Principal token |
| `DATABASE_URL` | No* | PostgreSQL connection string |
| `APP_ENV` | No | `development` / `staging` / `production` (default: `development`) |
| `CORS_ORIGINS` | No | Comma-separated allowed origins (default: `*`) |
| `DATABRICKS_MODEL_NAME` | No | Deployed model name in registry (default: `drug_efficacy_prod`) |

---

## Branching Strategy

We follow a **trunk-based development** model with short-lived feature branches.

```
dev       ← integration branch — everyone PRs here.
feature/...   ← individual work, branched from develop.
```

### Branch naming convention

```
feature/{STORY-ID}-{short-description}
```

### Examples

```
feature/DS-001-experiments-list
feature/DS-002-experiment-detail
feature/DS-003-experiment-runs
```

### Workflow

```bash
# Start a new feature
git checkout develop
git pull origin develop
git checkout -b feature/DS-001-experiments-list

# Work, commit, push
git add .
git commit -m "feat(DS-001): add GET /experiments endpoint with mock fallback"
git push origin feature/DS-001-experiments-list
`

### Commit message format

```
{type}({story-id}): {short description}

Types: feat | fix | refactor | test | docs | chore
```

Examples:
```
feat(DS-001): list experiments from Databricks with mock fallback
fix(DS-006): handle single run_id gracefully with 400 response
test(DS-005): add submission integration tests with SQLite
docs(readme): add branching strategy and setup instructions
```

---
