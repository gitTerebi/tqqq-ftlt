class Returns:
    def __init__(self, strategy):
        self.strategy = strategy
        self.start = strategy.broker.getvalue()
        self.end = self.start
        self.rtot = 0.0

    def next(self):
        self.end = self.strategy.broker.getvalue()

    def stop(self):
        if self.start != 0:
            self.rtot = (self.end / self.start) - 1.0

    def get_analysis(self):
        return {"rtot": self.rtot}
