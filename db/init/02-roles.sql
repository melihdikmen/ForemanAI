-- Read-only database role for the assistant (least privilege).
--
-- The agent's tools (fault history, manual search) connect as this role, so even if
-- the LLM is tricked by a prompt injection it physically cannot INSERT/UPDATE/DELETE.
-- Writes (work-order submit/approve) use the owner role via DATABASE_URL.
--
-- NOTE: this script runs only when the Postgres data volume is first created.
-- On an existing volume, run it manually: docker exec -i foremanai-db psql -U foreman -d foremanai < db/init/02-roles.sql

CREATE ROLE foreman_reader WITH LOGIN PASSWORD 'reader-local-only';

GRANT CONNECT ON DATABASE foremanai TO foreman_reader;
GRANT USAGE ON SCHEMA public TO foreman_reader;

-- Tables that already exist.
GRANT SELECT ON ALL TABLES IN SCHEMA public TO foreman_reader;

-- Tables created later by Alembic migrations (run as the owner role `foreman`).
-- Without this, every new migration would silently hide its table from the reader.
ALTER DEFAULT PRIVILEGES FOR ROLE foreman IN SCHEMA public
    GRANT SELECT ON TABLES TO foreman_reader;
