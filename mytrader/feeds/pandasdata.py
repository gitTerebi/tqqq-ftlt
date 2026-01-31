class Line:
    def __init__(self, data, col):
        self.data = data
        self.col = col

    def __getitem__(self, idx):
        i = self.data.idx + idx

        # before first bar or after last bar → Backtrader returns nan
        if i < 0 or i >= len(self.data.df):
            return float("nan")

        return self.data.df.iloc[i][self.col]


class DateTimeLine:
    def __init__(self, data):
        self.data = data

    def date(self, _):
        return self.data.df.iloc[self.data.idx].name.date()

    def datetime(self, _):
        i = self.data.idx

        # before first bar or after last bar → return None
        if i < 0 or i >= len(self.data.df):
            return None

        ts = self.data.df.iloc[i].name

        # index may already be datetime
        try:
            return ts.to_pydatetime()
        except AttributeError:
            return ts


class PandasData:
    def __init__(self, dataname):
        self.df = dataname
        self.idx = -1

        # normalize columns (case-insensitive)
        cols = {c.lower(): c for c in self.df.columns}

        def col(name):
            key = name.lower()
            if key not in cols:
                raise KeyError(f"PandasData missing column: {name}")
            return cols[key]

        self.open = Line(self, col("open"))
        self.high = Line(self, col("high"))
        self.low = Line(self, col("low"))
        self.close = Line(self, col("close"))

        self.datetime = DateTimeLine(self)

    def __len__(self):
        return len(self.df)

    def _advance(self, idx: int):
        self.idx = idx

    def __getitem__(self, idx):
        i = self.data.idx + idx

        # before first bar or after last bar → Backtrader returns nan
        if i < 0 or i >= len(self.data.df):
            return float("nan")

        return self.data.df.iloc[i][self.col]

    def _advance_to_date(self, dt):
        if dt in self.df.index:
            self.idx = self.df.index.get_loc(dt)
        # else: keep idx unchanged (carry-forward)
