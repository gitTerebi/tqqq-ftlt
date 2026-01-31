class DrawDown:
    def __init__(self, strategy):
        self.strategy = strategy
        self.max = type("DD", (), {})()
        self.max.drawdown = 0.0
        self.max.moneydown = 0.0
        self.max.len = 0
        self._peak = strategy.broker.getvalue()
        self._len = 0

    def next(self):
        v = self.strategy.broker.getvalue()
        if v > self._peak:
            self._peak = v
            self._len = 0
            return
        dd = (self._peak - v) / self._peak * 100.0
        self._len += 1
        if dd > self.max.drawdown:
            self.max.drawdown = dd
            self.max.moneydown = self._peak - v
            self.max.len = self._len

    def stop(self):
        pass

    def get_analysis(self):
        return self
