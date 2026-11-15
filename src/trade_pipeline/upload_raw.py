"""Выгрузка сырых файлов Comtrade в S3. Запуск: python -m trade_pipeline.upload_raw"""

import logging
from pathlib import Path

import boto3

from trade_pipeline.config import load_settings
from trade_pipeline.logging_setup import setup_logging

logger = logging.getLogger(__name__)

RAW_DIR = Path("data/raw/comtrade")
PREFIX = "raw/comtrade"


def s3_key(path: Path) -> str:
    period = path.stem.split("_")[-1]
    return f"{PREFIX}/period={period}/{path.name}"


def main() -> None:
    settings = load_settings()
    setup_logging(settings.log_level)

    s3 = boto3.client("s3")
    files = sorted(RAW_DIR.glob("*.json"))
    for path in files:
        key = s3_key(path)
        s3.upload_file(str(path), settings.s3_bucket, key)
        logger.info("Uploaded %s -> s3://%s/%s", path.name, settings.s3_bucket, key)
    logger.info("Done: %d files uploaded", len(files))


if __name__ == "__main__":
    main()