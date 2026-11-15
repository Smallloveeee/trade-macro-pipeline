FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir .

COPY alembic.ini ./
COPY migrations ./migrations

CMD ["python", "-m", "trade_pipeline.consume_trade"]