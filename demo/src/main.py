import datetime
import json
import pathlib
from typing import Iterator

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import DataTable, Footer, Header

from . import domain, task_1


def main(
    source: str,
    task: str,
    config: pathlib.Path | None = None,
) -> None:
    match task:
        case "task_1":
            method = task_1.compute
        case _:
            raise ValueError(f"Invalid task: {task}")

    kwargs = {}
    if config is not None:
        with open(config, "r") as file:
            kwargs = json.load(file)

    app = LiveDataApp(generator=method(source, **kwargs))
    app.run()


class LiveDataApp(App):
    """A Textual app to display live updating data."""

    # Bind keys to actions. "q" will quit the app.
    BINDINGS = [("q", "quit", "Quit")]

    def __init__(self, generator: Iterator[domain.Result]):
        self._generator = generator
        super().__init__()

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        with Container():
            yield DataTable()
        yield Footer()

    def on_mount(self) -> None:
        """Called when the app is first mounted."""
        # Get the DataTable widget
        table = self.query_one(DataTable)
        table.add_columns("Field", "Value")
        self.set_interval(0.3, self.update_data)

    def update_data(self) -> None:
        """Method to update the table with new data."""
        # Get the DataTable widget
        table = self.query_one(DataTable)

        result = next(self._generator)

        table.clear()
        table.add_row("Value", f"{result.value:.4f}")
        table.add_row(
            "Newest Considered", result.newest_considered.strftime("%Y-%m-%d %H:%M:%S")
        )
        table.add_row(
            "Oldest Considered", result.oldest_considered.strftime("%Y-%m-%d %H:%M:%S")
        )
        table.add_row(
            "Last updated", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )


def _cli() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=str)
    parser.add_argument("--task", type=str, default="task_1")
    parser.add_argument("--config", type=pathlib.Path, default=None)
    args = parser.parse_args()

    main(args.source, args.task, args.config)


if __name__ == "__main__":
    _cli()