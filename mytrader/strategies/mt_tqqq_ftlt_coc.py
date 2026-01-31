import mytrader as bt
from enum import Enum, auto
from functions.inverted_holdings_logger import InvertedHoldingsLog
from mytrader.mt_base_strategy import MTBaseStrategy
from functions.portfolio_reporting import log_monthly_deployed


class State(Enum):
    BULL_TQQQ = auto()
    BULL_HEDGE_UVXY = auto()
    BEAR_OVERSOLD_TECH = auto()
    BEAR_OVERSOLD_SPXL = auto()
    BEAR_VOL_SPIKE = auto()
    BEAR_TQQQ_TREND = auto()
    BEAR_DEFENSIVE_SQQQ = auto()
    BEAR_DEFENSIVE_BSV = auto()


class MT_TQQQFTLT_COC(MTBaseStrategy):
    params = dict(
        rsi_period=10,
        ma200_period=200,
        ma20_period=20,
        report="reports/mt_tqqq_ftlt_coc.html"
    )

    def __init__(self):
        super().__init__()

        # -------- Data feeds --------
        self.spy = self.getdatabyname("SPY")
        self.tqqq = self.getdatabyname("TQQQ")
        self.spxl = self.getdatabyname("SPXL")
        self.uvxy = self.getdatabyname("UVXY")
        self.tecl = self.getdatabyname("TECL")
        self.sqqq = self.getdatabyname("SQQQ")
        self.bsv = self.getdatabyname("BSV")

        self.ALL_ASSETS = [
            self.bsv, self.spxl, self.sqqq,
            self.tecl, self.tqqq, self.uvxy
        ]

        # -------- Indicators --------
        self.spy_ma200 = bt.ind.SMA(self.spy, period=self.p.ma200_period)
        self.tqqq_ma20 = bt.ind.SMA(self.tqqq, period=self.p.ma20_period)

        self.rsi_spy = bt.ind.RSI(self.spy, period=self.p.rsi_period)
        self.rsi_tqqq = bt.ind.RSI(self.tqqq, period=self.p.rsi_period)
        self.rsi_spxl = bt.ind.RSI(self.spxl, period=self.p.rsi_period)
        self.rsi_uvxy = bt.ind.RSI(self.uvxy, period=self.p.rsi_period)
        self.rsi_sqqq = bt.ind.RSI(self.sqqq, period=self.p.rsi_period)
        self.rsi_bsv = bt.ind.RSI(self.bsv, period=self.p.rsi_period)

        self.state = None

        # -------- Reporting --------
        self.start_portfolio_value = self.broker.getvalue()
        self.prev_portfolio_value = self.broker.getvalue()
        self.min_portfolio_value = self.broker.getvalue()

        self.hlog = InvertedHoldingsLog(self.p.report)
        self.hlog.clear()

    # =========================
    # FSM Resolver
    # =========================
    def resolve_state(self):
        if self.spy.close[0] > self.spy_ma200[0]:
            if self.rsi_tqqq[0] > 79 or self.rsi_spxl[0] > 80:
                return State.BULL_HEDGE_UVXY
            return State.BULL_TQQQ

        if self.rsi_tqqq[0] < 31:
            return State.BEAR_OVERSOLD_TECH

        if self.rsi_spy[0] < 30:
            return State.BEAR_OVERSOLD_SPXL

        if self.rsi_uvxy[0] > 84:
            if self.tqqq.close[0] > self.tqqq_ma20[0]:
                return State.BEAR_TQQQ_TREND
            if self.rsi_sqqq[0] > self.rsi_bsv[0]:
                return State.BEAR_DEFENSIVE_SQQQ
            else:
                return State.BEAR_DEFENSIVE_BSV

        if self.rsi_uvxy[0] > 74:
            return State.BEAR_VOL_SPIKE

        if self.tqqq.close[0] > self.tqqq_ma20[0]:
            return State.BEAR_TQQQ_TREND

        if self.rsi_sqqq[0] > self.rsi_bsv[0]:
            return State.BEAR_DEFENSIVE_SQQQ
        else:
            return State.BEAR_DEFENSIVE_BSV

    def asset_for_state(self, state):
        return {
            State.BULL_TQQQ: self.tqqq,
            State.BULL_HEDGE_UVXY: self.uvxy,
            State.BEAR_OVERSOLD_TECH: self.tecl,
            State.BEAR_OVERSOLD_SPXL: self.spxl,
            State.BEAR_VOL_SPIKE: self.uvxy,
            State.BEAR_TQQQ_TREND: self.tqqq,
            State.BEAR_DEFENSIVE_SQQQ: self.sqqq,
            State.BEAR_DEFENSIVE_BSV: self.bsv
        }[state]

    def log_state_resolution(self):
        # 1️⃣ SPY above 200 SMA → bull regime
        if self.spy.close[0] > self.spy_ma200[0]:
            if self.rsi_tqqq[0] > 79 or self.rsi_spxl[0] > 80:
                self.log(
                    f"STATE=BULL_HEDGE_UVXY "
                    f"(SPY={self.spy.close[0]:.1f}>{self.spy_ma200[0]:.1f}) "
                    f"(RSI_TQQQ={self.rsi_tqqq[0]:.1f}>79 "
                    f"OR RSI_SPXL={self.rsi_spxl[0]:.1f}>80)"
                )
                return
            else:
                self.log(
                    f"STATE=BULL_TQQQ "
                    f"(SPY={self.spy.close[0]:.1f}>{self.spy_ma200[0]:.1f})"
                    f"(RSI_TQQQ={self.rsi_tqqq[0]:.1f}<79 "
                    f"OR RSI_SPXL={self.rsi_spxl[0]:.1f}<80)"
                )
                return

        # 2️⃣ Oversold tech
        if self.rsi_tqqq[0] < 31:
            self.log(
                f"STATE=BEAR_OVERSOLD_TECH "
                f"(RSI_TQQQ={self.rsi_tqqq[0]:.1f}<31)"
            )
            return

        # 3️⃣ Oversold SPY
        if self.rsi_spy[0] < 30:
            self.log(
                f"STATE=BEAR_OVERSOLD_SPXL "
                f"(RSI_SPY={self.rsi_spy[0]:.1f}<30)"
            )
            return

        # 4️⃣ Extreme volatility
        if self.rsi_uvxy[0] > 84:
            if self.tqqq.close[0] > self.tqqq_ma20[0]:
                self.log(
                    f"STATE=BEAR_TQQQ_TREND "
                    f"(RSI_UVXY={self.rsi_uvxy[0]:.1f}>84) "
                    f"(TQQQ={self.tqqq.close[0]:.1f}>{self.tqqq_ma20[0]:.1f})"
                )
                return

            if self.rsi_sqqq[0] > self.rsi_bsv[0]:
                self.log(
                    f"STATE=BEAR_DEFENSIVE_SQQQ "
                    f"(RSI_UVXY={self.rsi_uvxy[0]:.1f}>84) "
                    f"(RSI_SQQQ={self.rsi_sqqq[0]:.1f}>"
                    f"RSI_BSV={self.rsi_bsv[0]:.1f})"
                )
                return
            else:
                self.log(
                    f"STATE=BEAR_DEFENSIVE_BSV "
                    f"(RSI_UVXY={self.rsi_uvxy[0]:.1f}>84) "
                    f"(RSI_BSV={self.rsi_bsv[0]:.1f}>="
                    f"RSI_SQQQ={self.rsi_sqqq[0]:.1f})"
                )
                return

        # 5️⃣ Moderate volatility
        if self.rsi_uvxy[0] > 74:
            self.log(
                f"STATE=BEAR_VOL_SPIKE "
                f"(RSI_UVXY={self.rsi_uvxy[0]:.1f}>74)"
            )
            return

        # 6️⃣ Trend fallback
        if self.tqqq.close[0] > self.tqqq_ma20[0]:
            self.log(
                f"STATE=BEAR_TQQQ_TREND "
                f"(TQQQ={self.tqqq.close[0]:.1f}>{self.tqqq_ma20[0]:.1f})"
            )
            return

        # 7️⃣ Defensive fallback
        if self.rsi_sqqq[0] > self.rsi_bsv[0]:
            self.log(
                f"STATE=BEAR_DEFENSIVE_SQQQ "
                f"(RSI_SQQQ={self.rsi_sqqq[0]:.1f}>"
                f"RSI_BSV={self.rsi_bsv[0]:.1f})"
            )
            return
        else:
            self.log(
                f"STATE=BEAR_DEFENSIVE_BSV "
                f"(RSI_BSV={self.rsi_bsv[0]:.1f}>="
                f"RSI_SQQQ={self.rsi_sqqq[0]:.1f})"
            )
            return

    # =========================
    # Main loop (DAILY, SAME-BAR SWAP)
    # =========================
    def next(self):
        self._update_drawdown()  # 👈 base infra

        if not self.trading_allowed():
            return

        next_state = self.resolve_state()
        next_asset = self.asset_for_state(next_state)

        # -------- REBALANCE USING CURRENT HOLDINGS (NO "current_asset" VAR) --------
        held_assets = [d for d in self.ALL_ASSETS if self.getposition(d).size != 0]

        self.log_state_resolution()

        growth_pct = ((self.broker.getvalue() - self.prev_portfolio_value) / self.prev_portfolio_value) * 100
        total_growth_pct = ((self.broker.getvalue() - self.start_portfolio_value) / self.start_portfolio_value) * 100

        self.hlog.collect(self,
                          assets=["CASH"] + self.ALL_ASSETS,
                          change=f"{growth_pct:+.2f}%",
                          value=f"{total_growth_pct:+,.1f}%",
                          notes=f"{next_state.name.replace('STATE', '')}"
                          )

        # -------- STATE CHANGE → TARGET REBALANCE --------
        if next_state != self.state:
            self.log(f"STATE CHANGE: {self.state} → {next_state}")

            #  Do nothing if asset is held already
            if len(held_assets) == 1 and held_assets[0] is next_asset:
                self.state = next_state
                return

            # 1️⃣ SELL FIRST (no exectype!)
            for d in held_assets:
                if d is not next_asset:
                    self.close(d)

            o = next_asset.open[0]
            h = next_asset.high[0]
            l = next_asset.low[0]
            c = next_asset.close[0]

            # Set target asset
            self.order_target_percent(next_asset, 1.0)
            self.log(f"ENTER {next_asset._name} @ 100% | DECISION OHLC O:{o:,.2f} H:{h:,.2f} L:{l:,.2f} C:{c:,.2f}")

            self.state = next_state

        log_monthly_deployed(strategy=self)
        self.log('')

    def stop(self):
        self.hlog.write()
