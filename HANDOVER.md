# HANDOVER.md — Runbook

How to operate ForemanAI without the person who built it. Everything here was executed at
least once; commands are copy-paste.

## 1. Where things are

| Thing | Where | Notes |
|---|---|---|
| Source | GitHub `melihdikmen/ForemanAI`, branch `master` | push to master = deploy (after the eval gate) |
| Service | Google Cloud Run `foremanai`, region `europe-west1`, project `foremanai-261127` | URL: https://foremanai-998448097011.europe-west1.run.app |
| Images | Artifact Registry `europe-west1-docker.pkg.dev/foremanai-261127/foremanai/api` | tags = git sha, plus `latest` |
| Database | Neon Postgres 16 + pgvector, project `foremanai` (billowing-tree-39931754), branch `production` | free tier; owner role `neondb_owner`, read-only role `foreman_reader` |
| Secrets (runtime) | Google Secret Manager: `OPENROUTER_API_KEY`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `DATABASE_URL`, `DATABASE_URL_READONLY` | bound to Cloud Run as env vars, `latest` version |
| Secrets (CI) | GitHub Actions secret `OPENROUTER_API_KEY` | the only GitHub secret; Google auth is keyless (WIF) |
| Traces | Langfuse cloud (EU), project keys in Secret Manager | every `/ask` returns `trace_id` |
| Logs | Cloud Logging, resource `cloud_run_revision`, service `foremanai` | |

Local developer copy of the cloud connection strings: `.env` keys `CLOUD_DATABASE_URL`,
`CLOUD_DATABASE_URL_READONLY` (never committed).

## 2. Deploy

**Normal path:** merge/push to `master`. GitHub Actions runs lint → pytest → eval gate
(`--min-accuracy 0.85` on the dev split) → builds the image tagged with the commit sha → deploys →
curls `/health`. ~12 minutes. Watch: https://github.com/melihdikmen/ForemanAI/actions

**Manual deploy from a laptop** (e.g. CI is down):

```bash
gcloud config set project foremanai-261127
gcloud auth configure-docker europe-west1-docker.pkg.dev
docker build -t europe-west1-docker.pkg.dev/foremanai-261127/foremanai/api:manual .
docker push europe-west1-docker.pkg.dev/foremanai-261127/foremanai/api:manual
gcloud run deploy foremanai --region europe-west1 \
  --image europe-west1-docker.pkg.dev/foremanai-261127/foremanai/api:manual --quiet
```

`gcloud run deploy --image` keeps the service's env vars and secrets; only the image changes.

**Rollback:** deploy an older sha (every commit on master has an image):

```bash
gcloud run revisions list --service foremanai --region europe-west1
gcloud run services update-traffic foremanai --region europe-west1 --to-revisions foremanai-00004-sgq=100
```

## 3. Secrets

Rotate a key: add a new secret *version*, then roll a new revision (running instances keep the
old value until restarted).

```bash
printf '%s' "$NEW_VALUE" | gcloud secrets versions add OPENROUTER_API_KEY --data-file=-
gcloud secrets versions access latest --secret OPENROUTER_API_KEY | wc -c    # sanity: length, no newline
gcloud run services update foremanai --region europe-west1 --update-labels rotated=$(date +%s)
```

**Never pipe a value with a trailing newline** (`echo` adds one). A newline inside the OpenRouter
key produced `Illegal header value` and a 500 on `/ask`; the traceback with the key landed in
Cloud Logging. Use `printf '%s'` or `tr -d '\r\n'`.

GitHub secret for CI: repo → Settings → Secrets and variables → Actions → `OPENROUTER_API_KEY`.

## 4. Database

Migrations run automatically at container start (`alembic upgrade head` in `docker/entrypoint.sh`).
New migration locally: `uv run alembic revision --autogenerate -m "..."`, review, commit.

**Re-seed the cloud DB** (synthetic data; this **deletes work orders**, fault records and
machines, then recreates them, then rebuilds the vector index):

```bash
export DATABASE_URL="$(grep '^CLOUD_DATABASE_URL=' .env | cut -d= -f2- | tr -d '\r')"
uv run python -m app.seed
uv run python -m app.rag.index
```

**Read-only role check** (should fail with `permission denied`):

```bash
export DATABASE_URL_READONLY="$(grep '^CLOUD_DATABASE_URL_READONLY=' .env | cut -d= -f2- | tr -d '\r')"
uv run python -c "from sqlalchemy import text; from app.db import ReadOnlySessionLocal as S
s=S(); s.execute(text(\"insert into machines (code,name) values ('X','x')\"))"
```

New Neon branch/database: run `db/init/01-extensions.sql`, then create `foreman_reader` with the
grants in `db/init/02-roles.sql` (use a random password, not the local one).

## 5. Evals and quality gate

- Dev split runs in CI on every push; the job fails below 85% raw accuracy. Single runs are noisy
  (±5 points on ~35 questions); if a push fails at 84% with no related change, re-run once before
  investigating.
- Reports: `evals/results/<tag>.md` + `<tag>.answers.jsonl`. CI uploads `ci.md` as an artifact.
- When a question fails, first read the answer in the `.answers.jsonl`. Historically most failures
  were scorer gaps (wording not in `must_include`/refusal hints), not wrong answers. Run
  `evals/judge.py` (needs `JUDGE_MODEL`) to get a second opinion before touching the prompt.
- Held-out split (`--split heldout`) only at phase ends. Do not tune on it.

## 6. Troubleshooting

| Symptom | Check | Likely cause |
|---|---|---|
| `/ask` 500, `/health` fine | Cloud Logging, severity ERROR | bad secret value (newline), OpenRouter outage, DB unreachable |
| New revision never becomes ready | revision logs: "failed to load /app/entrypoint.sh" | exec bit lost (fixed by `COPY --chmod=755`); or `alembic upgrade` failing against the DB |
| First request slow (15–20 s) | normal | cold start; set `--min-instances=1` (~$15/month) if unacceptable |
| Agent answers "tüm zamanlar" to a follow-up | request body | client did not send `history` |
| `list_recent_rejections` returns 0 on cloud | work_orders table | cloud DB not re-seeded since phase 11 |
| CI red at "Unit + API tests" on first run | GitHub secrets | `OPENROUTER_API_KEY` missing: `Settings()` fails to load |
| Deploy job: auth error | WIF pool `github`, provider `github-oidc` | repo renamed/moved: attribute condition `repository_owner == 'melihdikmen'` and binding to `melihdikmen/ForemanAI` |
| Langfuse shows nothing | Secret Manager keys, `LANGFUSE_HOST` | tracing is a no-op when keys are empty |

Useful log query:

```bash
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="foremanai" AND severity>=ERROR' \
  --project foremanai-261127 --freshness 1h --limit 20 --format 'value(timestamp,textPayload)'
```

## 7. MCP (Claude Desktop)

Config file (Windows Store build of Claude Desktop keeps it outside `%APPDATA%`):
`%LOCALAPPDATA%\Claude-Data\<package id>\claude_desktop_config.json`, otherwise
`%APPDATA%\Claude\claude_desktop_config.json`.

```json
{
  "mcpServers": {
    "foremanai": {
      "command": "C:\\Users\\<you>\\.local\\bin\\uv.exe",
      "args": ["run", "--directory", "D:\\Projects\\ForemanAI", "python", "-m", "app.mcp_server"]
    }
  }
}
```

Fully quit Claude Desktop (tray → Quit) and reopen; the server needs the local Docker DB running.
Through MCP the *client's* model interprets tool output: our system prompt and output guard are
not in that loop; the read-only role and draft-only tool still are.

## 8. Costs to watch

- OpenRouter: set a monthly limit on the key (the demo URL is public). ~$0.0012 per question.
- Cloud Run: scale-to-zero; `max-instances=2`, `concurrency=20` cap abuse.
- Neon free tier sleeps after inactivity; the first query after sleep adds ~1 s.

## 9. Tear-down

```bash
gcloud run services delete foremanai --region europe-west1
gcloud artifacts repositories delete foremanai --location europe-west1
for s in OPENROUTER_API_KEY LANGFUSE_PUBLIC_KEY LANGFUSE_SECRET_KEY DATABASE_URL DATABASE_URL_READONLY; do gcloud secrets delete $s --quiet; done
gcloud projects delete foremanai-261127      # removes WIF pool, service account, everything
neon projects delete billowing-tree-39931754
```
