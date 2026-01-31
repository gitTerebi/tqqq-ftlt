from mytrader.ind.indicator import Indicator


class _SMMA:
    """
    Exact Wilder SMMA as used by Backtrader (MovAv.Smoothed)
    """

    def __init__(self, period):
        self.period = period
        self._seed = []
        self._avg = None
        self._last_i = None

    def update(self, value, i):
        # already processed this bar
        if self._last_i == i:
            return self._avg

        # seeding phase (SMA)
        if self._avg is None:
            self._seed.append(value)

            if len(self._seed) < self.period:
                self._last_i = i
                return None

            self._avg = sum(self._seed) / self.period
            self._last_i = i
            return self._avg

        # Wilder smoothing
        self._avg = ((self._avg * (self.period - 1)) + value) / self.period
        self._last_i = i
        return self._avg


class RSI(Indicator):
    """
    Exact Backtrader RSI (RSI / RSI_Wilder / RSI_SMMA)

    This is a faithful, line-for-line semantic port of:

        backtrader.indicators.rsi.RelativeStrengthIndex
    """

    def __init__(self, data, period=14, lookback=1):
        super().__init__(data)

        self.data = data
        self.period = period
        self.lookback = lookback

        self._up_smma = _SMMA(period)
        self._down_smma = _SMMA(period)

        self._last_i = None
        self._last_rsi = float("nan")

    def __getitem__(self, idx):
        i = self.data.idx + idx

        # need previous bar
        if i < self.lookback:
            return float("nan")

        # already calculated this bar
        if self._last_i == i:
            return self._last_rsi

        # -------- UpDay / DownDay (EXACT)
        prev = self.data.close[-self.lookback]
        curr = self.data.close[0]

        up = max(curr - prev, 0.0)
        down = max(prev - curr, 0.0)

        # -------- Wilder SMMA
        avg_up = self._up_smma.update(up, i)
        avg_down = self._down_smma.update(down, i)

        # still seeding (should not happen after warmup)
        if avg_up is None or avg_down is None:
            self._last_i = i
            self._last_rsi = float("nan")
            return self._last_rsi

        # -------- RSI calculation (EXACT)
        if avg_down == 0.0:
            rsi = 100.0
        else:
            rs = avg_up / avg_down
            rsi = 100.0 - (100.0 / (1.0 + rs))

        self._last_i = i
        self._last_rsi = rsi
        return rsi
