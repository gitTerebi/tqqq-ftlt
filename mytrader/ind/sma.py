from mytrader.ind.indicator import Indicator


class SMA(Indicator):
    def __init__(self, data, period):
        super().__init__(data)
        self.data = data
        self.period = period

    def __getitem__(self, idx):
        i = self.data.idx + idx
        if i < self.period - 1:
            return float("nan")

        values = [
            self.data.close[j - i]
            for j in range(i - self.period + 1, i + 1)
        ]
        return float(sum(values) / self.period)
