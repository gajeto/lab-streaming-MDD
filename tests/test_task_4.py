import datetime
import json
import pathlib
import threading
from src import domain
from src.task_4 import compute

'''
Este test se aplica así:
batch_1: 3 eventos, 1 de interes que debe ser forwarded -> tasa de forwarded 1/3
batch_2: 2 nuevos eventos (5 en total ya), 1 de interes -> tasa de forwarded 2/5 = 0.4
'''
def test_task_4(tmp_path: pathlib.Path) -> None:
    source = tmp_path / 'source'
    source.mkdir(parents=True, exist_ok=True)

    # Interest file with the messages that should be forwarded
    interest_file = tmp_path / 'interest_messages.txt'
    interest_file.write_text(
        '\n'.join(
            [
                'HTTP Status Code: 500',
                'Alert: disk full',
            ]
        ),
        encoding='utf-8',
    )

    basetime = datetime.datetime.now()

    with open(source / 'batch_1.json', 'w', encoding='utf-8') as f:
        json.dump(
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
                    'message': 'HTTP Status Code: 404',
                },
            ],
            f,
        )

    stop = threading.Event()
    gen = compute(str(source), stop=stop, interest_file=str(interest_file), capacity=1000, error_rate=0.001)

    first = next(gen)
    # forwarded=1 (only 500), total=3 -> 1/3
    assert first == domain.Result(
        value=1 / 3,
        newest_considered=basetime + datetime.timedelta(seconds=20),
        oldest_considered=basetime + datetime.timedelta(seconds=0),
    )

    with open(source / 'batch_2.json', 'w', encoding='utf-8') as f:
        json.dump(
            [
                {
                    'service': 'svc',
                    'timestamp': (basetime + datetime.timedelta(seconds=70)).timestamp(),
                    'message': 'Alert: disk full', 
                },
                {
                    'service': 'svc',
                    'timestamp': (basetime + datetime.timedelta(seconds=80)).timestamp(),
                    'message': 'HTTP Status Code: 200',
                },
            ],
            f,
        )

    second = next(gen)
    # forwarded=2 (500, disk full), total=5 -> 0.4
    assert second == domain.Result(
        value=0.4,
        newest_considered=basetime + datetime.timedelta(seconds=80),
        oldest_considered=basetime + datetime.timedelta(seconds=0),
    )

    stop.set()
