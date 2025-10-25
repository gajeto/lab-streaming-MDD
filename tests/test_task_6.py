import json
import os, shutil
import datetime
import threading
import pathlib

from src.task_6 import compute


def _write_json(path, rows):
    with open(path, 'w', encoding='utf-8') as f:
        for r in rows:
            f.write(json.dumps(r) + '\n')


def _is_domain_result(obj) -> bool:
    return (
        hasattr(obj, 'value')
        and hasattr(obj, 'newest_considered')
        and hasattr(obj, 'oldest_considered')
        and isinstance(obj.value, (int, float))
    )

def test_task_6(tmp_path: pathlib.Path) -> None:
    # 1) Build a temp directory with NDJSON (files layout only)
    source = tmp_path / 'source'
    source.mkdir(parents=True, exist_ok=True)

    basetime = datetime.datetime.now()
    # Two files (simulate two micro-batches); within the same small window
    batch_1 = [
        {'service': 'api', 'timestamp': (basetime).timestamp(), 'message': 'HTTP Status Code: 200'},
        {'service': 'api', 'timestamp': (basetime).timestamp(), 'message': 'HTTP Status Code: 500'},
        {'service': 'etl', 'timestamp': (basetime).timestamp(), 'message': 'HTTP Status Code: 404'},
    ]
    batch_2 = [
        {'service': 'api', 'timestamp': (basetime + datetime.timedelta(seconds=3)).timestamp(), 'message': 'HTTP Status Code: 503'},
        {'service': 'etl', 'timestamp': (basetime + datetime.timedelta(seconds=3)).timestamp(), 'message': 'HTTP Status Code: 200'},
    ]

    _write_json(os.path.join(source, 'batch_1.json'), batch_1)
    _write_json(os.path.join(source, 'batch_2.json'), batch_2)

    # 2) Drive compute() as a streaming generator with a stop Event
    stop = threading.Event()
    generator = compute(str(source), stop=stop)

    # Collect until we’ve seen both expected error rates, then stop
    results = []
    seen_api = False  # expect ≈ 2/3
    seen_etl = False  # expect = 1/2

    for r in generator:
        assert _is_domain_result(r), 'Output does not match domain.Result contract'
        results.append(r)

        v = float(r.value)
        if abs(v - (2 / 3)) <= 1e-3:
            seen_api = True
        if abs(v - 0.5) <= 1e-3:
            seen_etl = True

        # Once both per-service rates surfaced, we can stop the stream
        if seen_api and seen_etl:
            stop.set()
            break

    # 3) Assertions
    assert results, 'task_6.compute should yield at least one domain.Result'
    assert seen_api, 'Expected API error_rate ≈ 0.666..., but it was not observed'
    assert seen_etl, 'Expected ETL error_rate = 0.5, but it was not observed'

    # Optional temporal sanity (only if comparable)
    for r in results:
        try:
            assert r.newest_considered >= r.oldest_considered
        except TypeError:
            pass

    # 4) Cleanup
    shutil.rmtree(source, ignore_errors=True)
