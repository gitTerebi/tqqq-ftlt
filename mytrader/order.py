class Order:
    BUY, SELL = range(2)

    Created, Submitted, Accepted, Completed, Canceled, Margin, Rejected = range(7)

    def __init__(self, data, *, side, size=None, target_pct=None, price=None, strategy=None):
        """
        side:
            Order.BUY  -> target-percent intent (size computed at execution)
            Order.SELL -> size-based close/reduction (exact size)
        """
        self.data = data
        self.strategy = strategy
        self.side = side

        self.created = type("Created", (), {})()
        self.created.price = price

        # SELL = exact size
        if side == Order.SELL:
            self.created.size = size  # negative number

        # BUY = intent
        elif side == Order.BUY:
            self.created.target_pct = target_pct

        else:
            raise ValueError("Invalid order side")

        self.status = Order.Submitted

        self.executed = type("Executed", (), {})()
        self.executed.size = 0.0
        self.executed.price = 0.0
        self.executed.dt = None

    def isbuy(self):
        return self.executed.size > 0

    def issell(self):
        return self.executed.size < 0

    def getstatusname(self):
        return [
            "Created", "Submitted", "Accepted", "Completed",
            "Canceled", "Margin", "Rejected"
        ][self.status]
