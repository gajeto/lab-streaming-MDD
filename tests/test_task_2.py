import datetime
import json
import pathlib
import threading

from src import domain
from src.task_2 import compute

'''
Este test se aplica así:
batch_1: 2 eventos, uno exitoso (200) y otro fallido a los 30s (500) -> tasa de error 0.5
batch_2: un nuevo evento a los 70s (404), el evento a los 0s cae fuera de la ventana.
Ahora ya son 2 eventos fallidos-> tasa de error 1.0
'''

def test_task_2(tmp_path: pathlib.Path) -> None:
    source = tmp_path / 'source'
    source.mkdir(parents=True, exist_ok=True)

    basetime = datetime.datetime.now()
    with open(source / 'batch_1.json', 'w') as f:
        json.dump(
            [
                {
                    'service': 'svc',
                    'timestamp': (basetime + datetime.timedelta(seconds=0)).timestamp(),
                    'message': 'HTTP Status Code: 200',
                },
                {
                    'service': 'svc',
                    'timestamp': (basetime + datetime.timedelta(seconds=30)).timestamp(),
                    'message': 'HTTP Status Code: 500',
                },
            ],
            f,
        )

    stop = threading.Event()
    gen = compute(str(source), stop=stop)

    first = next(gen)
    assert first == domain.Result(
        value=1/2,
        newest_considered=basetime + datetime.timedelta(seconds=30),
        oldest_considered=basetime + datetime.timedelta(seconds=0),
    )
    with open(source / 'batch_2.json', 'w') as f:
        json.dump(
            [
                {
                    'service': 'svc',
                    'timestamp': (basetime + datetime.timedelta(seconds=70)).timestamp(),
                    'message': 'HTTP Status Code: 404',
                },
            ],
            f,
        )

    second = next(gen)
    assert second == domain.Result(
        value=1.0,
        newest_considered=basetime + datetime.timedelta(seconds=70),
        oldest_considered=basetime + datetime.timedelta(seconds=30),
    )

    stop.set()
