"""Trade & Macro pipeline: Comtrade -> S3 -> Kafka -> PostgreSQL -> DQ checks."""

from datetime import datetime, timedelta

from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import DAG

PIPELINE = "/opt/pipeline/bin/python -m trade_pipeline."
WORKDIR = "/opt/airflow"

with DAG(
    dag_id="trade_pipeline",
    schedule="@weekly",
    start_date=datetime(2026, 11, 1),
    catchup=False,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=1)},
    tags=["trade"],
) as dag:
    migrate = BashOperator(
        task_id="migrate",
        bash_command="cd /opt/pipeline-src && /opt/pipeline/bin/alembic upgrade head",
    )
    fetch = BashOperator(
        task_id="fetch_comtrade", bash_command=PIPELINE + "fetch_trade", cwd=WORKDIR
    )
    upload = BashOperator(
        task_id="upload_raw_to_s3", bash_command=PIPELINE + "upload_raw", cwd=WORKDIR
    )
    produce = BashOperator(
        task_id="produce_to_kafka", bash_command=PIPELINE + "produce_trade", cwd=WORKDIR
    )
    consume = BashOperator(
        task_id="consume_to_postgres", bash_command=PIPELINE + "consume_trade", cwd=WORKDIR
    )
    dq = BashOperator(task_id="dq_checks", bash_command=PIPELINE + "check_mirror")

    fetch >> upload >> produce >> consume >> dq
    migrate >> consume