import datetime
import json
import pathlib
import threading

from src import domain
from src.task_5.task_5 import compute


def _write_json(path: pathlib.Path, rows: list[dict]) -> None:
    with path.open('w', encoding='utf-8') as f:
        for r in rows:
            f.write(json.dumps(r) + '\n')


def test_task_5(tmp_path: pathlib.Path) -> None:
    source = tmp_path / 'source'
    source.mkdir(parents=True, exist_ok=True)

    basetime = datetime.datetime.now()

    # Batch 1: 3 logs, one unsuccessful (500), value = 1/3
    batch1 = source / 'batch_1.ndjson'
    _write_json(
        batch1,
        [
            {
                'service': 'svc',
                'timestamp': (basetime + datetime.timedelta(seconds=0)).timestamp(),
                'message': 'HTTP Status Code: 200',
            },
            {
                'service': 'svc',
                'timestamp': (basetime + datetime.timedelta(seconds=10)).timestamp(),
                'message': 'HTTP Status Code: 500',
            },
            {
                'service': 'svc',
                'timestamp': (basetime + datetime.timedelta(seconds=20)).timestamp(),
                'message': 'HTTP Status Code: 200',
            },
        ],
    )

    stop = threading.Event()
    gen = compute(str(source), stop=stop)

    first = next(gen)
    assert first == domain.Result(
        value=1 / 3,
        newest_considered=basetime + datetime.timedelta(seconds=20),
        oldest_considered=basetime + datetime.timedelta(seconds=0),
    )

    # Batch 2: 2 logs, both unsuccessful,  value = 1.0
    batch2 = source / 'batch_2.ndjson'
    _write_json(
        batch2,
        [
            {
                'service': 'svc',
                'timestamp': (basetime + datetime.timedelta(seconds=75)).timestamp(),
                'message': 'HTTP Status Code: 404',
            },
            {
                'service': 'svc',
                'timestamp': (basetime + datetime.timedelta(seconds=85)).timestamp(),
                'message': 'HTTP Status Code: 500',
            },
        ],
    )

    second = next(gen)
    assert second == domain.Result(
        value=1.0,
        newest_considered=basetime + datetime.timedelta(seconds=85),
        oldest_considered=basetime + datetime.timedelta(seconds=75),
    )

    stop.set()
