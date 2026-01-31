# context.py
import threading

_ctx = threading.local()


def get_current_strategy():
    return getattr(_ctx, "current_strategy", None)


class StrategyContext:
    def __init__(self, strategy):
        self.strategy = strategy

    def __enter__(self):
        _ctx.current_strategy = self.strategy

    def __exit__(self, exc_type, exc, tb):
        _ctx.current_strategy = None
