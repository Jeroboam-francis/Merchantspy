# Airtel Merchant Analytics

Enterprise-oriented merchant analytics platform using FastAPI, SQLAlchemy, Oracle, and a React 19 dashboard.

## Run locally

Requirements: Python 3.11+, Node.js 20+, and Docker (optional).

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
Copy-Item backend\.env.example backend\.env
uvicorn app.main:app --app-dir backend --reload
```

In another terminal:

```powershell
cd frontend
npm install
npm run dev
```

The API is at `http://localhost:8000`, Swagger UI at `/docs`, and the frontend at `http://localhost:5173`. Development defaults to SQLite. Set `DATABASE_URL` to an Oracle SQLAlchemy URL (for example `oracle+oracledb://user:password@host:1521/?service_name=FREEPDB1`) to use Oracle; install `oracledb` from `backend/requirements-oracle.txt`.

The development login is controlled by `SEED_ADMIN_EMAIL` and `SEED_ADMIN_PASSWORD`. Change these values before any non-local deployment. To create the full deterministic-scale sample workload (100 merchants, 50,000 subscribers, and 500,000 transactions over 24 months), run:

```powershell
python backend\scripts\seed_demo.py
```

The seeder inserts in batches and refuses to run if transaction data already exists, preventing accidental duplicate loads. Its `--small` option creates a quick smoke-test dataset. The full seed is intentionally separate from API startup.

## Services and operations

`docker compose up --build` starts the API, frontend, and Oracle Free. Configure secrets through environment variables; never commit production credentials. Apply `database/oracle_schema.sql` to provision the Oracle schema. The application uses SQLAlchemy metadata for development startup and the Oracle script for production schema management.

The API exposes `/api/v1/auth`, `/api/v1/analytics`, `/api/v1/merchants`, `/api/v1/transactions`, `/api/v1/collections`, `/api/v1/disbursements`, `/api/v1/forecasts`, `/api/v1/reports`, and `/api/v1/admin`. JWT bearer tokens use role-based authorization (`admin`, `manager`, `analyst`, `viewer`). Only admin, manager, and analyst roles can initiate persisted anomaly detection. API docs are disabled by setting `ENABLE_API_DOCS=false` and are always disabled in production mode.

ML uses statsmodels ARIMA and scikit-learn Random Forest/Isolation Forest models. Prophet is available by installing `backend/requirements-prophet.txt`. Forecasting validates the model and minimum history, stores results, and returns confidence bounds. Dashboard metrics poll at 60-second intervals; anomaly signals are recalculated every five minutes. PDF, Excel, and CSV export endpoints stream generated reports. No data is sent to external services.

Merchant score is a transparent weighted index: revenue 40%, successful transactions 25%, subscriber count 20%, and 30-day growth 15%. Each input is normalized to a 0–100 component; growth is neutral (50) when a comparison period has no revenue. Score bands map to A+ (90+), A (80+), B+ (70+), B (60+), C (45+), and D. This baseline should be calibrated to Airtel's approved business definitions before operational use.

## Design and production notes

- `backend/app` contains API, configuration, database session, ORM entities, auth, service and ML layers.
- `frontend/src` follows pages/components/layouts/hooks/services/context/assets/styles.
- `database/oracle_schema.sql` defines core entities, constraints, indexes, reporting views, and a stored procedure.
- `.github/workflows/ci.yml` runs Python tests/compile checks, builds the frontend, and publishes version-tagged containers to GHCR.
- Replace `DATABASE_URL`, JWT key, CORS origins, and credentials using deployment secrets without code changes.
- Set the GitHub Actions repository variable `VITE_API_BASE_URL` before publishing a version tag; the release workflow fails rather than publishing a frontend with a development API URL.

Before production, provision managed Oracle, apply schema changes through a controlled release, use a secret manager and TLS termination, configure an identity provider/key rotation, observability and alerting, backups/retention, connection pooling, and load-test against representative Oracle volumes. Production startup fails closed if the default JWT key, admin credentials, SQLite URL, or localhost CORS origins are configured. Sample user passwords and the development JWT key are not suitable for production.
