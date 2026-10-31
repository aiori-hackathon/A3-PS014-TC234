# NetCompare

Responsive internet-quality pilot dashboard for measuring and comparing end-to-end network quality across participant-reported access media. The frontend is live-only: it shows empty states until a configured measurement agent submits real records.

## Requirements
- Node.js 20+ and npm
- Docker Desktop (for the included local PostgreSQL setup), or PostgreSQL 14+
- Python 3.10+ for the measurement agent

## Start the app locally
1. With Docker Desktop running, run `powershell -ExecutionPolicy Bypass -File .\start-backend.ps1` from the project root. It creates local credentials, starts PostgreSQL, syncs and generates the Prisma client, creates tables, and launches the API. Or use the manual steps below. The database persists in a Docker volume.
2. In `backend/`, copy `.env.example` to `.env`. For the included local Docker database, keep the example `DATABASE_URL`; replace both bearer tokens with long random values before connecting any agents.
3. In `backend/`, run `npm install`, then `npm run prisma:generate`, then `npm run prisma:migrate`.
4. Start the API from `backend/` with `npm run dev`. It listens at `http://localhost:4000`; `GET /api/health` reports whether the database is connected.
5. In `frontend/`, run `npm install` once, then `npm run dev`. Open `http://localhost:5173`.
6. To connect an endpoint, install `measurement-agent/requirements.txt`, copy `measurement-agent/.env.example` to `.env`, set its participant ID and agent token, and run `python agent.py --once` for a single collection.

If Docker is not installed, install PostgreSQL 17 from an elevated PowerShell with `winget install --id PostgreSQL.PostgreSQL.17 -e`. Then change `DATABASE_URL` in `backend/.env` to your PostgreSQL user, password, and database (for the installer default database, use `postgres` as the database name). The API cannot store registrations or measurements until a PostgreSQL server is reachable and the schema has been pushed.

## Components
- `frontend/`: React, Vite, React Router, Recharts and Lucide.
- `backend/`: Express REST API, Zod validation, Prisma Client and cron schedule worker.
- `database/schema.prisma`: canonical PostgreSQL schema; `backend/scripts/sync-schema.js` prepares the generated-client output path before Prisma commands.
- `measurement-agent/`: Python endpoint agent.
- `documentation/`: measurement notes and API guide.

## REST API
- `GET /api/health`
- `POST /api/participants` (consent required)
- `GET|PATCH /api/participants` (admin bearer token)
- `POST /api/measurements` (agent bearer token)
- `GET /api/measurements`, `GET /api/analytics/summary` (admin bearer token)
- `GET|POST /api/schedules` (admin bearer token)
- `POST /api/reports/export` (admin bearer token; CSV)

The worker enqueues due schedule jobs in PostgreSQL. An agent job consumer is still needed for remote scheduling; participants can also run the agent at their agreed interval. The browser does not perform measurements or run schedules.

## Measurement and privacy limits
Measurements reflect the volunteer device, local network, ISP path and test conditions. The agent caps downloads; uploads require an operator-controlled endpoint. Loaded jitter currently uses an unloaded RTT variation proxy and should not be described as a controlled loaded-jitter test. Access medium is participant-reported or human-verified, never inferred from IP. Use minimal location data and informed participant consent. Repeated measures from a participant are correlated; use endpoint-level summaries or cluster-aware uncertainty intervals.

## Production checklist
Use HTTPS, strong secrets, backups, rate limits, key rotation, data retention/deletion rules, a durable schedule-job consumer, monitored agent health, and a server-side PDF renderer. The admin UI is not yet wired to the authenticated API. The provided Docker password is for local development only.
