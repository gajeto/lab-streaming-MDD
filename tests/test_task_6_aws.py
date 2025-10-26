# tests/test_task_6_s3.py
import json
import datetime
import threading
import uuid
import os

import boto3
import pytest

from src.task_6 import compute  # or from src import task_6; then task_6.compute

BUCKET = os.environ.get("TEST_BUCKET", "test-data-streaming-mdd")  # set via env/CI

def _put_ndjson(s3, bucket: str, key: str, rows: list[dict]) -> None:
    body = "\n".join(json.dumps(r) for r in rows)
    s3.put_object(Bucket=bucket, Key=key, Body=body.encode("utf-8"))

@pytest.mark.timeout(60)
def test_task_6_s3_streaming():
    # 1) Unique S3 prefixes for this test run
    run_id = uuid.uuid4().hex
    source_prefix = f"task6/{run_id}/source/"
    ckpt_prefix   = f"task6/{run_id}/checkpoints/"

    s3 = boto3.client("s3")

    # 2) Create two tiny NDJSON “batches” in the same window
    basetime = datetime.datetime.now(datetime.timezone.utc)
    batch_1 = [
        {"service": "api", "timestamp": basetime.timestamp(), "message": "HTTP Status Code: 200"},
        {"service": "api", "timestamp": basetime.timestamp(), "message": "HTTP Status Code: 500"},
        {"service": "etl", "timestamp": basetime.timestamp(), "message": "HTTP Status Code: 404"},
    ]
    batch_2 = [
        {"service": "api", "timestamp": (basetime + datetime.timedelta(seconds=3)).timestamp(), "message": "HTTP Status Code: 503"},
        {"service": "etl", "timestamp": (basetime + datetime.timedelta(seconds=3)).timestamp(), "message": "HTTP Status Code: 200"},
    ]

    # 3) Upload to S3 as NDJSON
    _put_ndjson(s3, BUCKET, source_prefix + "batch_1.json", batch_1)
    _put_ndjson(s3, BUCKET, source_prefix + "batch_2.json", batch_2)

    # 4) Run the streaming compute against S3 + checkpoint on S3
    stop = threading.Event()
    gen = compute(
        source=f"s3://{BUCKET}/{source_prefix}",
        stop=stop,
        checkpoint=f"s3://{BUCKET}/{ckpt_prefix}"
    )

    # 5) Collect until we observe the expected window math
    results, seen_api, seen_etl = [], False, False
    for r in gen:
        results.append(r)
        v = float(r.value)
        if abs(v - 2/3) <= 1e-3: seen_api = True   # api: 200,500,503 -> 2/3 errors
        if abs(v - 0.5) <= 1e-3: seen_etl = True   # etl: 404,200    -> 1/2 errors
        if seen_api and seen_etl:
            stop.set()
            break

    assert results, 'task_6.compute should yield at least one domain.Result'
    assert seen_api, 'Expected API error_rate ≈ 0.666..., but it was not observed'
    assert seen_etl, 'Expected ETL error_rate = 0.5, but it was not observed'

    # 6) (Optional) cleanup S3 objects for this test run
    #     Keeping it simple: use a delete-objects batch (or leave for lifecycle rules).
    try:
        s3.delete_objects(
            Bucket=BUCKET,
            Delete={
                "Objects": [
                    {"Key": source_prefix + "batch_1.json"},
                    {"Key": source_prefix + "batch_2.json"},
                ]
            },
        )
    except Exception:
        # Non-fatal in tests; checkpoint cleanup is typically handled by lifecycle policies
        pass
