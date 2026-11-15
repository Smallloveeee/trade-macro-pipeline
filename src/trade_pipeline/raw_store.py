"""Чтение сырых ответов Comtrade: с локального диска или из S3."""

import json
import logging
from collections.abc import Iterator
from pathlib import Path

import boto3

logger = logging.getLogger(__name__)

RAW_DIR = Path("data/raw/comtrade")
S3_PREFIX = "raw/comtrade/"


def iter_local(raw_dir: Path = RAW_DIR) -> Iterator[dict]:
    for path in sorted(raw_dir.glob("*.json")):
        yield json.loads(path.read_text())


def iter_s3(bucket: str, prefix: str = S3_PREFIX) -> Iterator[dict]:
    s3 = boto3.client("s3")
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            body = s3.get_object(Bucket=bucket, Key=obj["Key"])["Body"].read()
            logger.info("Read s3://%s/%s", bucket, obj["Key"])
            yield json.loads(body)