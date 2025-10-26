import datetime
import json
import pathlib
import threading

from src import domain
from src.task_3 import compute


def test_task_3_simple(tmp_path: pathlib.Path) -> None:
    source = tmp_path / "source"
    source.mkdir(parents=True, exist_ok=True)

    basetime = datetime.datetime.now()

    # Batch 1: three events
    # Codes: [200, 500, 200] -> mode should be 200
    with open(source / "batch_1.json", "w") as f:
        json.dump(
            [
                {
                    "service": "svc",
                    "timestamp": (basetime + datetime.timedelta(seconds=0)).timestamp(),
                    "message": "HTTP Status Code: 200",
                },
                {
                    "service": "svc",
                    "timestamp": (basetime + datetime.timedelta(seconds=10)).timestamp(),
                    "message": "HTTP Status Code: 500",
                },
                {
                    "service": "svc",
                    "timestamp": (basetime + datetime.timedelta(seconds=20)).timestamp(),
                    "message": "HTTP Status Code: 200",
                },
            ],
            f,
        )

    stop = threading.Event()
    # k=5 equals total events written across both batches -> deterministic mode
    gen = compute(str(source), stop=stop, k=5, random_seed=42)

    first = next(gen)
    assert first == domain.Result(
        value=200.0,  # mode code as float
        newest_considered=basetime + datetime.timedelta(seconds=20),
        oldest_considered=basetime + datetime.timedelta(seconds=0),
    )

    # Batch 2: two more events
    # Now total codes: [200, 500, 200, 404, 500] -> 200 (2), 500 (2), 404 (1)
    # Tie between 200 and 500 => choose the smaller code deterministically (200)
    with open(source / "batch_2.json", "w") as f:
        json.dump(
            [
                {
                    "service": "svc",
                    "timestamp": (basetime + datetime.timedelta(seconds=70)).timestamp(),
                    "message": "HTTP Status Code: 404",
                },
                {
                    "service": "svc",
                    "timestamp": (basetime + datetime.timedelta(seconds=80)).timestamp(),
                    "message": "HTTP Status Code: 500",
                },
            ],
            f,
        )

    second = next(gen)
    assert second == domain.Result(
        value=200.0,
        newest_considered=basetime + datetime.timedelta(seconds=80),
        oldest_considered=basetime + datetime.timedelta(seconds=0),
    )

    stop.set()
