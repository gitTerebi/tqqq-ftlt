def log_monthly_deployed(
        strategy,
):
    """
    Logs monthly deployed / cash / total / growth metrics.

    Parameters
    ----------
    strategy : bt.Strategy
        The calling strategy instance (self)
    """

    def current_positions(strat):
        # Strategy-agnostic: look at all data feeds and return those with a non-zero position
        positions = []
        for data in getattr(strat, "datas", []):
            try:
                if strat.getposition(data).size != 0:
                    positions.append(data)
            except Exception:
                # If a feed can't be queried for any reason, skip it (keeps reporting robust)
                continue
        return positions

    # --- current positions
    current_positions = current_positions(strategy)

    # --- cash & deployment
    cash = strategy.broker.getcash()
    portfolio_value = strategy.broker.getvalue()
    deployed = portfolio_value - cash

    # --- growth calculations
    growth_pct = (
                         (portfolio_value - strategy.prev_portfolio_value)
                         / strategy.prev_portfolio_value
                 ) * 100

    total_growth_pct = (
                               (portfolio_value - strategy.start_portfolio_value)
                               / strategy.start_portfolio_value
                       ) * 100

    # --- position percentage log
    positions_log = []
    for data in current_positions:
        pos = strategy.getposition(data)
        pos_value = abs(pos.size) * data.close[0]
        percent = (pos_value / portfolio_value) * 100
        positions_log.append(f"{data._name}: {percent:.1f}%")

    # --- per-symbol logging (ONE LINE EACH)
    if current_positions:
        for data in current_positions:
            pos = strategy.getposition(data)

            pos_value = abs(pos.size) * data.close[0]
            percent = (pos_value / portfolio_value) * 100

            o, h, l, c = (
                data.open[0],
                data.high[0],
                data.low[0],
                data.close[0],
            )

            strategy.log(f"---- {data._name}: {percent:.1f}% | O:{o:,.2f} H:{h:,.2f} L:{l:,.2f} C:{c:,.2f}")

    # --- logging output (UNCHANGED FORMAT)
    if positions_log:
        strategy.log(
            f'---- {", ".join(positions_log)} '
            f'(Deployed: ${deployed:,.2f}) (Cash: ${cash:,.2f}) '
            f'(Total: ${portfolio_value:,.2f}) '
            f'(Change: {growth_pct:+.2f}%) '
            f'(Total Growth: {total_growth_pct:+.2f}%)'
        )
    else:
        strategy.log(
            f'---- None (Deployed: $0.00) (Cash: ${cash:,.2f}) '
            f'(Total: ${portfolio_value:,.2f}) '
            f'(Change: {growth_pct:+.2f}%) '
            f'(Total Growth: {total_growth_pct:+.2f}%)'
        )

    strategy.prev_portfolio_value = strategy.broker.getvalue()
