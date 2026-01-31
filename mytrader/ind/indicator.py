from mytrader.context import get_current_strategy


class Indicator:
    def __init__(self, data):
        self.data = data

        # 🔑 auto-register using construction context
        strategy = get_current_strategy()
        if strategy is not None:
            if not hasattr(strategy, "_indicators"):
                strategy._indicators = []
            strategy._indicators.append(self)
