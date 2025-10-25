import datetime
import json
import pathlib
import threading

from src import domain
from src.task_2 import compute

"""Define the test of a sliding window algorithm that computes the rate of unsuccessful requests over the last minute
Create a series of events with timestamps and HTTP status codes,
then another series of events and compare the computed results with the expected ones.
"""

def test_task_2_no_overlapping(tmp_path: pathlib.Path) -> None:
    source = tmp_path / "source"
    source.mkdir(parents=True, exist_ok=True)
    basetime = datetime.datetime.now()
    # Create events for the first batch with a incremental timestamp
    with open(source / "batch_1.json", "w") as file:
        json.dump(
            [
                {
                    "service": "monitoring",
                    "timestamp": (
                        basetime + datetime.timedelta(seconds=10)
                    ).timestamp(),
                    "message": "HTTP Status Code: 200",
                },
                {
                    "service": "monitoring",
                    "timestamp": (
                        basetime + datetime.timedelta(seconds=20)
                    ).timestamp(),
                    "message": "HTTP Status Code: 500",
                },
                {
                    "service": "monitoring",
                    "timestamp": (
                        basetime + datetime.timedelta(seconds=30)
                    ).timestamp(),
                    "message": "HTTP Status Code: 400",
                },
            ],
            file,
        )

    stop = threading.Event()
    generator = compute(str(source), stop=stop)
    first = next(generator)

    with open(source / "batch_2.json", "w") as file:
        json.dump(
            [
                {
                    "service": "monitoring",
                    "timestamp": (
                        basetime + datetime.timedelta(seconds=70)
                    ).timestamp(),
                    "message": "HTTP Status Code: 200",
                },
                {
                    "service": "monitoring",
                    "timestamp": (
                        basetime + datetime.timedelta(seconds=80)
                    ).timestamp(),
                    "message": "HTTP Status Code: 503",
                },
            ],
            file,
        )

    
    second = next(generator)

    assert first == domain.Result(
        value=2/3,
        newest_considered=basetime + datetime.timedelta(seconds=30),
        oldest_considered=basetime + datetime.timedelta(seconds=10),
    )

    assert second == domain.Result(
        value=0.5,
        newest_considered=basetime + datetime.timedelta(seconds=80),
        oldest_considered=basetime + datetime.timedelta(seconds=10),
    )

    stop.set()

def test_task_2_overlapping(tmp_path: pathlib.Path) -> None:
    source = tmp_path / "source"
    source.mkdir(parents=True, exist_ok=True)
    basetime = datetime.datetime.now()
    # Create events for the first batch with a incremental timestamp
    with open(source / "batch_1.json", "w") as file:
        json.dump(
            [
                {
                    "service": "monitoring",
                    "timestamp": (
                        basetime + datetime.timedelta(seconds=10)
                    ).timestamp(),
                    "message": "HTTP Status Code: 200",
                },
                {
                    "service": "monitoring",
                    "timestamp": (
                        basetime + datetime.timedelta(seconds=20)
                    ).timestamp(),
                    "message": "HTTP Status Code: 500",
                },
                {
                    "service": "monitoring",
                    "timestamp": (
                        basetime + datetime.timedelta(seconds=30)
                    ).timestamp(),
                    "message": "HTTP Status Code: 400",
                },
            ],
            file,
        )

    stop = threading.Event()
    generator = compute(str(source), stop=stop)
    first = next(generator)

    with open(source / "batch_2.json", "w") as file:
        json.dump(
            [
                {
                    "service": "monitoring",
                    "timestamp": (
                        basetime + datetime.timedelta(seconds=50)
                    ).timestamp(),
                    "message": "HTTP Status Code: 200",
                },
                {
                    "service": "monitoring",
                    "timestamp": (
                        basetime + datetime.timedelta(seconds=60)
                    ).timestamp(),
                    "message": "HTTP Status Code: 503",
                },
            ],
            file,
        )

    second = next(generator)

    assert first == domain.Result(
        value=2/3,
        newest_considered=basetime + datetime.timedelta(seconds=30),
        oldest_considered=basetime + datetime.timedelta(seconds=10),
    )

    assert second == domain.Result(
        value=3/5,
        newest_considered=basetime + datetime.timedelta(seconds=60),
        oldest_considered=basetime + datetime.timedelta(seconds=10),
    )

    stop.set()

def test_task_3_overlapping(tmp_path: pathlib.Path) -> None:
    source = tmp_path / "source"
    source.mkdir(parents=True, exist_ok=True)
    basetime = datetime.datetime.now()
    # Create events for the first batch with a incremental timestamp
    with open(source / "batch_1.json", "w") as file:
        json.dump(
            [
                {
                    "service": "monitoring",
                    "timestamp": (
                        basetime + datetime.timedelta(seconds=10)
                    ).timestamp(),
                    "message": "HTTP Status Code: 200",
                },
                {
                    "service": "monitoring",
                    "timestamp": (
                        basetime + datetime.timedelta(seconds=20)
                    ).timestamp(),
                    "message": "HTTP Status Code: 500",
                },
                {
                    "service": "monitoring",
                    "timestamp": (
                        basetime + datetime.timedelta(seconds=30)
                    ).timestamp(),
                    "message": "HTTP Status Code: 400",
                },
            ],
            file,
        )

    stop = threading.Event()
    generator = compute(str(source), stop=stop)
    first = next(generator)

    with open(source / "batch_2.json", "w") as file:
        json.dump(
            [
                {
                    "service": "monitoring",
                    "timestamp": (
                        basetime + datetime.timedelta(seconds=60)
                    ).timestamp(),
                    "message": "HTTP Status Code: 200",
                },
                {
                    "service": "monitoring",
                    "timestamp": (
                        basetime + datetime.timedelta(seconds=70)
                    ).timestamp(),
                    "message": "HTTP Status Code: 503",
                },
                {
                    "service": "monitoring",
                    "timestamp": (
                        basetime + datetime.timedelta(seconds=80)
                    ).timestamp(),
                    "message": "HTTP Status Code: 400",
                },
            ],
            file,
        )

    second = next(generator)

    assert first == domain.Result(
        value=2/2,
        newest_considered=basetime + datetime.timedelta(seconds=30),
        oldest_considered=basetime + datetime.timedelta(seconds=20),
    )

    assert second == domain.Result(
        value=4/5,
        newest_considered=basetime + datetime.timedelta(seconds=80),
        oldest_considered=basetime + datetime.timedelta(seconds=20),
    )

    stop.set()