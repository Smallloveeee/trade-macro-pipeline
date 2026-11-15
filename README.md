# Trade & Macro Data Pipeline

A data pipeline on public **UN Comtrade** and **ECB** data that detects **mirror trade gaps** — differences between what country A reports as exports to B and what B reports as imports from A. Large, persistent gaps are used in illicit financial flow statistics as a signal of possible trade misinvoicing.

## Architecture

```
UN Comtrade API ─┐                          ┌─► PostgreSQL ─► SQL: mirror gaps
ECB FX API ──────┴─► clients ─► raw JSON ─► Kafka ─► consumer (DQ checks)
                     (retries)   (cache)            └─► dead-letter topic
```

- **Clients** — fetch (I/O, timeouts, retries with exponential backoff for 429/5xx/timeouts) separated from pure parse functions.
- **Kafka** — producer keyed by the data grain; consumer validates each record, sends bad ones to a dead-letter topic, writes good ones in batches and commits offsets only after the database commit (at-least-once + idempotent upsert = no duplicates).
- **PostgreSQL** — schema managed with Alembic (plain SQL, reversible migrations), primary key = grain, `NUMERIC` for money, `CHECK` constraints, idempotent `INSERT ... ON CONFLICT DO UPDATE`.
- **Docker Compose** — Postgres, Kafka and the pipeline steps (migrate → producer → consumer) start with one command.

## Run

```bash
docker compose up --build
```

Then query the gaps:

```bash
docker exec -i trade-postgres psql -U trade -d trade < sql/mirror_gap.sql
```

Fetching fresh data from Comtrade needs a free API key in `.env` (see `.env.example`) and `python -m trade_pipeline.load_trade`.

## Findings worth knowing

- **Data grain.** One Comtrade request returned 24 rows for a single trade flow — the same value broken down by customs regime, transport mode and second partner in all combinations. Summing them overstates trade 8×. The parser keeps only the total row and validates exactly one per key.
- **Control case.** Mineral fuels, Germany → China, 2023: +4.1% gap, within the normal CIF/FOB margin.
- **Flagged ≠ proven.** The largest gaps are in HS chapter 71 (precious metals). Before calling anything suspicious: CIF/FOB, origin vs consignment, transit, timing and too broad commodity codes. Next step: drill down to HS 7108 (gold).

## Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
ruff check . && pytest
```

Unit tests run without network: HTTP calls and `sleep` are mocked.