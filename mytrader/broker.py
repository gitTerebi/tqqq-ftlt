from .order import Order
from .position import Position


class Broker:
    def __init__(self, cash):
        self.cash = float(cash)
        self.positions = {}
        self.pending = []
        self.use_open = False

    def submit(self, order):
        self.pending.append(order)
        return order

    def getposition(self, data):
        return self.positions.setdefault(data, Position())

    def getcash(self):
        return self.cash

    def setcash(self, cash):
        self.cash = float(cash)

    def getvalue(self):
        value = self.cash
        for d, p in self.positions.items():
            if p.size != 0 and getattr(d, "idx", -1) >= 0:
                value += p.size * d.close[0]
        return value

    def execute_pending(self):
        # 1️⃣ execute all SELL orders
        for o in list(self.pending):
            if o.side == Order.SELL:
                self._execute_sell(o)

        # 2️⃣ execute all BUY orders
        for o in list(self.pending):
            if o.side == Order.BUY:
                self._execute_buy(o)

        self.pending.clear()

    def _execute_sell(self, o):

        # Use open price of the day?
        if self.use_open:
            price = o.data.open[0]
        else:
            price = o.created.price

        pos = self.getposition(o.data)

        size = o.created.size  # already negative

        if pos.size == 0:
            return

        cost = size * price
        self.cash -= cost

        # HARD CLOSE (Backtrader semantics)
        pos.size = 0.0

        o.status = Order.Completed
        o.executed.size = size
        o.executed.price = price
        o.executed.dt = o.data.datetime.datetime(0)

        o.strategy.notify_order(o)

    def _execute_buy(self, o):

        # Use open price of the day?
        if self.use_open:
            price = o.data.open[0]
        else:
            price = o.created.price

        pos = self.getposition(o.data)

        portfolio_value = self.getvalue()
        target_value = portfolio_value * o.created.target_pct
        current_value = pos.size * price
        delta_value = target_value - current_value

        # already at target
        if abs(delta_value) < 1e-12:
            return

        size = delta_value / price

        # BUY only
        if size <= 0:
            return

        # enforce cash
        size = min(size, self.cash / price)

        # integer when possible
        if size >= 1:
            size = int(size)

        if abs(size) < 1e-12:
            return

        cost = size * price
        self.cash -= cost
        pos.size += size

        # snapshot execution values ONCE
        exec_dt = o.data.datetime.datetime(0)
        exec_price = price
        exec_size = size

        o.status = Order.Completed
        o.executed.size = exec_size
        o.executed.price = exec_price
        o.executed.dt = exec_dt

        o.strategy.notify_order(o)
