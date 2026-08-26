import logging

from rich.logging import RichHandler


def setup_logging(level: int = logging.INFO) -> None:
    root = logging.getLogger("ch")
    if root.handlers:
        return
    handler = RichHandler(rich_tracebacks=True, show_path=False)
    handler.setFormatter(logging.Formatter("%(message)s"))
    root.addHandler(handler)
    root.setLevel(level)


logger = logging.getLogger("ch")
setup_logging()
