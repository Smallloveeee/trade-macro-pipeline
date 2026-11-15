from pathlib import Path

from trade_pipeline.upload_raw import s3_key


def test_s3_key_uses_period_partition():
    key = s3_key(Path("data/raw/comtrade/276_156_X_27_2023.json"))

    assert key == "raw/comtrade/period=2023/276_156_X_27_2023.json"