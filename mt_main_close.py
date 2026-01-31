from datetime import date
import mytrader as bt

from functions.download_with_retry import download_with_retry
from mytrader.strategies.mt_tqqq_ftlt_coc import MT_TQQQFTLT_COC

STARTING_CASH = 10000
START_DATE = '2011-01-01'
END_DATE = '2025-12-31'
TRADE_DATE = '2012-01-01'


STRATEGIES_TO_RUN = ['MT_TQQQFTLT_COC']

STRATEGY_CLASSES = {
    "MT_TQQQFTLT_COC": MT_TQQQFTLT_COC,
}

# -----------------------
# Download market data ONCE
# -----------------------
TICKERS = ['SPY', 'TQQQ', 'SPXL', 'UVXY', 'TECL', 'SQQQ', 'BSV', 'SOXL']

DATA_FRAMES = download_with_retry(TICKERS, START_DATE, END_DATE)


# Setup common for both strategies
def setup_cerebro():
    cerebro = bt.Cerebro()

    cerebro.broker.setcash(STARTING_CASH)

    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='dd')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')

    # Add data feeds
    for ticker, df in DATA_FRAMES.items():
        data = bt.feeds.PandasData(dataname=df)
        cerebro.adddata(data, name=ticker)

    return cerebro


# Run strategies dynamically
results = {}

for strategy_name in STRATEGIES_TO_RUN:
    print(f"\nRunning {strategy_name}...")
    cerebro = setup_cerebro()
    strategy_class = STRATEGY_CLASSES[strategy_name]
    cerebro.addstrategy(
        strategy_class,
        trade_start=date.fromisoformat(TRADE_DATE)
    )
    result = cerebro.run()

    final_value = cerebro.broker.getvalue()
    min_portfolio_value = result[0].min_portfolio_value
    dd = result[0].analyzers.getbyname('dd').get_analysis()
    max_dd_pct = dd.max.drawdown
    returns = result[0].analyzers.getbyname('returns').get_analysis()
    strat = result[0]

    # Manually compute CAR using trading bars (start date != trade date)
    start_dt = date.fromisoformat(TRADE_DATE)
    end_dt = date.fromisoformat(END_DATE)
    years = (end_dt - start_dt).days / 365.25
    annual_return = ((final_value / STARTING_CASH) ** (1 / years) - 1) * 100

    results[strategy_name] = {
        'final_value': final_value,
        'gain_pct': ((final_value - STARTING_CASH) / STARTING_CASH) * 100,
        'annual_return': annual_return,
        'min_portfolio_value': strat.max_dd_value,
        'max_dd_pct': strat.max_dd_pct,
        'max_dd_date': strat.max_dd_date,
    }

# Print individual results
print("\nIndividual Results:")
for name, data in results.items():
    dd_date = (
        data['max_dd_date'].strftime("%Y-%m-%d")
        if data.get('max_dd_date') is not None
        else "N/A"
    )

    print(
        f"{name} Final Value: ${data['final_value']:,.2f}, "
        f"Gain: {data['gain_pct']:,.2f}%, "
        f"CAR: {data['annual_return']:.2f}%, "
        f"Max Drawdown: ${data['min_portfolio_value']:,.2f} "
        f"(-{data['max_dd_pct']:.2f}%) on {dd_date}"
    )

# Comparison if more than one strategy
if len(results) > 1:
    print("\nComparison:")
    strategy_names = list(results.keys())
    for i in range(len(strategy_names)):
        for j in range(i + 1, len(strategy_names)):
            name1 = strategy_names[i]
            name2 = strategy_names[j]
            diff = results[name1]['final_value'] - results[name2]['final_value']
            pct_diff = (diff / results[name2]['final_value']) * 100 if results[name2]['final_value'] != 0 else 0
            print(f"[{name1}] vs [{name2}]: Difference: ${diff:.2f}, Percentage Difference: {pct_diff:.2f}%")
            if diff > 0:
                print(f"Winner: [{name1}]")
            elif diff < 0:
                print(f"Winner: [{name2}]")
            else:
                print(f"[{name1}] and [{name2}] performed equally.")
