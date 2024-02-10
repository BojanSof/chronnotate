from PyQt6.QtCore import QSignalBlocker


class SignalBlocker(QSignalBlocker):
    """Wrapper to use QSignalBlocker as a context manager in PySide2."""

    def __enter__(self):
        if hasattr(super(), "__enter__"):
            super().__enter__()
        else:
            super().reblock()

    def __exit__(self, exc_type, exc_value, traceback):
        if hasattr(super(), "__exit__"):
            super().__exit__(exc_type, exc_value, traceback)
        else:
            super().unblock()
