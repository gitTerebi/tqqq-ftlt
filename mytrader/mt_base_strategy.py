import mytrader as bt


class MTBaseStrategy(bt.Strategy):
    params = dict(
        trade_start=None,  # 👈 global gate (date or None)
    )

    def __init__(self):
        # --- drawdown state (HARD RESET PER RUN) ---
        v = self.broker.getvalue()
        self.peak_value = v
        self.max_dd_pct = 0.0
        self.max_dd_date = None
        self.max_dd_value = v
        self.min_portfolio_value = v

        # --- trading gate ---
        self._trading_enabled = False

    def _evaluate_indicators(self):
        for ind in getattr(self, "_indicators", []):
            try:
                _ = ind[0]
            except Exception:
                pass

    # =========================
    # Max Drawdown Tracker
    # =========================
    def _update_drawdown(self):
        # ❌ DO NOT TRACK DD BEFORE TRADING STARTS
        if not self.trading_allowed():
            return

        current_value = self.broker.getvalue()
        dt = self.datas[0].datetime.date(0)

        # Update peak
        if current_value > self.peak_value:
            self.peak_value = current_value
            return

        # Compute drawdown
        dd_pct = (self.peak_value - current_value) / self.peak_value * 100.0

        if dd_pct > self.max_dd_pct:
            self.max_dd_pct = dd_pct
            self.max_dd_date = dt
            self.max_dd_value = current_value

        self.min_portfolio_value = min(self.min_portfolio_value, self.broker.getvalue())

    # =========================
    # Trading gate
    # =========================
    def trading_allowed(self) -> bool:
        """
        Returns True only after trade_start date.
        Safe even if __init__ was not called.
        """
        if self.p.trade_start is None:
            return True

        today = self.datas[0].datetime.date(0)

        if today < self.p.trade_start:
            return False

        if not self._trading_enabled:
            self.log(f"TRADING ENABLED on {today}")
            self._trading_enabled = True

        return True

    def log(self, txt, dt=None):
        if not hasattr(self, "log_lines"):
            self.log_lines = []

        dt = dt or self.datas[0].datetime.date(0)
        formatted_dt = dt.strftime("%Y-%m-%d")
        line = f"{formatted_dt}, {txt}"

        self.log_lines.append(line)
        print(line)

    def _format_ohlc(self, data):
        try:
            return (
                f"O:{data.open[0]:,.2f} "
                f"H:{data.high[0]:,.2f} "
                f"L:{data.low[0]:,.2f} "
                f"C:{data.close[0]:,.2f}"
            )
        except Exception:
            return None

    # =========================
    # Order logging only
    # =========================
    def notify_order(self, order):
        if order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(
                "\n".join([
                    f"!!!!! {order.getstatusname()} for {order.data._name} size: {order.size} price: {order.created.price:,.2f} "
                    f"cash req: {order.created.size * order.created.price if order.created.price else 'N/A'}",
                ])
            )
            return

        # keep your Completed logic below (or return)
        if order.status != order.Completed:
            return

        total = order.executed.price * order.executed.size
        ohlc = self._format_ohlc(order.data)

        dt = bt.num2date(order.executed.dt)
        dt_str = dt.strftime("%Y-%m-%d") if dt is not None else "N/A"

        side = "BUY" if order.isbuy() else "SELL"
        msg = (
            f"{side} EXECUTED: {order.data._name} "
            f"at {order.executed.price:,.2f}, "
            f"size {order.executed.size}, "
            f"total {total:,.2f}, "
            f"time {dt_str}, "
            f"cash ${self.broker.getcash():,.2f}"
        )
        if ohlc:
            msg = f"{msg} | {ohlc}"

        self.log(msg)
