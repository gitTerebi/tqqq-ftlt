from .broker import Broker
from .context import StrategyContext

class Cerebro:
    def __init__(self, cash=10000.0):
        self.datas = []
        self.datasbyname = {}
        self._strategies = []
        self._analyzers = []
        self.broker = Broker(cash)

    def adddata(self, data, name=None):
        data._name = name
        self.datas.append(data)
        if name:
            self.datasbyname[name] = data

    def addstrategy(self, stratcls, **params):
        self._strategies.append((stratcls, params))

    def addanalyzer(self, analyzercls, _name=None):
        self._analyzers.append((_name, analyzercls))

    def run(self):
        strategies = []

        for stratcls, params in self._strategies:
            # 1️⃣ Allocate WITHOUT calling __init__
            strat = stratcls.__new__(stratcls)

            # 2️⃣ Inject engine context BEFORE __init__
            strat.broker = self.broker
            strat.cerebro = self
            strat.datas = self.datas
            strat.data = self.datas[0]
            strat.data0 = self.datas[0]
            strat.datetime = strat.data.datetime

            # 3️⃣ Backtrader-style params
            strat.p = type("Params", (), strat.params | params)()

            # 4️⃣ NOW call user __init__
            with StrategyContext(strat):
                strat.__init__()

            # 5️⃣ Init analyzers
            strat._init_analyzers(self._analyzers)

            strategies.append(strat)

        # Use first data as master clock (Backtrader default)
        master = self.datas[0]
        dates = master.df.index

        for dt in dates:
            # advance each data by DATE, not index
            for d in self.datas:
                d._advance_to_date(dt)

            self.broker.execute_pending()

            for strat in strategies:
                strat._evaluate_indicators()
                strat.next()
                for a in strat.analyzers.values():
                    a.next()

        for strat in strategies:
            for a in strat.analyzers.values():
                a.stop()
            strat.stop()

        return strategies
