import datetime
import json
import pathlib
import threading

from src import domain
from src.task_1 import compute


def test_task_1(tmp_path: pathlib.Path) -> None:
    source = tmp_path / "source"
    source.mkdir(parents=True, exist_ok=True)
    basetime = datetime.datetime.now()
    with open(source / "batch_1.json", "w") as file:
        json.dump(
            [
                {
                    "service": "monitoring",
                    "timestamp": (
                        basetime + datetime.timedelta(seconds=48)
                    ).timestamp(),
                    "message": "HTTP Status Code: 200",
                },
                {
                    "service": "monitoring",
                    "timestamp": (
                        basetime + datetime.timedelta(seconds=96)
                    ).timestamp(),
                    "message": "HTTP Status Code: 500",
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
                        basetime + datetime.timedelta(seconds=144)
                    ).timestamp(),
                    "message": "HTTP Status Code: 200",
                },
            ],
            file,
        )

    second = next(generator)

    assert first == domain.Result(
        value=0.5,
        newest_considered=basetime + datetime.timedelta(seconds=96),
        oldest_considered=basetime + datetime.timedelta(seconds=48),
    )

    assert second == domain.Result(
        value=2/3,
        newest_considered=basetime + datetime.timedelta(seconds=144),
        oldest_considered=basetime + datetime.timedelta(seconds=48),
    )

    stop.set()