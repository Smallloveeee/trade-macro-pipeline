import json

from trade_pipeline.raw_store import iter_local


def test_iter_local_reads_all_json_files(tmp_path):
    (tmp_path / "a.json").write_text(json.dumps({"data": [1]}))
    (tmp_path / "b.json").write_text(json.dumps({"data": [2]}))
    (tmp_path / "notes.txt").write_text("ignore me")

    payloads = list(iter_local(tmp_path))

    assert payloads == [{"data": [1]}, {"data": [2]}]