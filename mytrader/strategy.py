from .order import Order

class AnalyzerCollection(dict):
    def getbyname(self, name):
        return self[name]

class Strategy:
    params = {}
    def __init__(self, **kwargs):
        self.p = type("Params", (), self.params | kwargs)()

    def _init_analyzers(self, analyzers):
        self.analyzers = AnalyzerCollection()
        for name, cls in analyzers:
            inst = cls(self)
            if name:
                self.analyzers[name] = inst

    def __len__(self):
        return len(self.data)

    def getdatabyname(self, name):
        return self.cerebro.datasbyname[name]

    def getposition(self, data):
        return self.broker.getposition(data)

    def close(self, data=None):
        data = data or self.data
        pos = self.getposition(data)

        if pos.size != 0:
            self.broker.submit(
                Order(
                    data=data,
                    side=Order.SELL,
                    size=-pos.size,  # exact hard close
                    price=data.close[0],
                    strategy=self
                )
            )

    def order_target_percent(self, data, target_pct):
        self.broker.submit(
            Order(
                data=data,
                side=Order.BUY,
                target_pct=target_pct,  # intent only
                price=data.close[0],
                strategy=self
            )
        )

    def next(self): pass
    def stop(self): pass
    def notify_order(self, order): pass
    def notify_trade(self, trade): pass
