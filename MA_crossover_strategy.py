import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from logbook import Logger

from catalyst import run_algorithm
from catalyst.api import order_target_percent, record, symbol
from catalyst.exchange.utils.stats_utils import extract_transactions

NAMESPACE = "dual_moving_average"
log = Logger(NAMESPACE)

def initialize(context):
    # define asset
    context.asset = symbol("btc_usd")

    # amount of bars at specified timeframe
    context.i = 0

    # beginning price
    context.base_price = None

def handle_data(context, data):

    # define moving averages
    short = 20
    long = 50

    # skip bars until long window to properly compute MA
    context.i += 1
    if context.i < long:
        return

    # Compute moving averages with data.history() // see documentation for parameters
    short_data = data.history(context.asset,
                             "price",
                             bar_count = short,
                             frequency = "1T")
    short_ma = short_data.mean()

    long_data = data.history(context.asset,
                             "price",
                             bar_count = long,
                             frequency = "1T")
    long_ma = long_data.mean()

    # handy variable for current price
    price = data.current(context.asset, "price")

    # if the base price is not set, use the current value
    # base_price is the price at the first bar, used to calculate price change
    if context.base_price is None:
        context.base_price = price

    price_change = (price - context.base_price) / context.base_price

    # save values for inspection
    record(price = price,
           cash = context.portfolio.cash,
           price_change = price_change,
           short_ma = short_ma,
           long_ma = long_ma)

    # since we're using limit orders, wait until all orders are
    # executed before moving on
    orders = context.blotter.open_orders
    if len(orders) > 0:
        return

    # exit if we cannot trade
    if not data.can_trade(context.asset):
        return

    # check position (long or short)
    pos_amount = context.portfolio.positions[context.asset].amount

    # strategy logic
    if short_ma > long_ma and pos_amount == 0:

        # buy 100% of portfolio
        order_target_percent(context.asset, 1)

    elif short_ma < long_ma and pos_amount > 0:

        # sell complete position
        order_target_percent(context.asset, 0)

def analyze(context, perf):
    # Get the quote_currency that was passed as a parameter to the simulation
    exchange = list(context.exchanges.values())[0]
    quote_currency = exchange.base_currency.upper()

    # First chart: Plot portfolio value using quote_currency
    ax1 = plt.subplot(411)
    perf.loc[:, ['portfolio_value']].plot(ax=ax1)
    ax1.legend_.remove()
    ax1.set_ylabel('Portfolio Value\n({})'.format(quote_currency))
    start, end = ax1.get_ylim()
    ax1.yaxis.set_ticks(np.arange(start, end, (end - start) / 5))

    # Second chart: Plot asset price, moving averages and buys/sells
    ax2 = plt.subplot(412, sharex=ax1)
    perf.loc[:, ['price', 'short_ma', 'long_ma']].plot(ax = ax2, label = 'Price')
    ax2.legend_.remove()
    ax2.set_ylabel('{asset}\n({quote})'.format(asset = context.asset.symbol, quote = quote_currency
    ))
    start, end = ax2.get_ylim()
    ax2.yaxis.set_ticks(np.arange(start, end, (end - start) / 5))

    transaction_df = extract_transactions(perf)
    if not transaction_df.empty:
        buy_df = transaction_df[transaction_df['amount'] > 0]
        sell_df = transaction_df[transaction_df['amount'] < 0]
        ax2.scatter(
            buy_df.index.to_pydatetime(),
            perf.loc[buy_df.index, 'price'],
            marker = '^',
            s = 100,
            c = 'green',
            label = ''
        )
        ax2.scatter(
            sell_df.index.to_pydatetime(),
            perf.loc[sell_df.index, 'price'],
            marker = 'v',
            s = 100,
            c = 'red',
            label = ''
        )

    # Third chart: Compare percentage change between our portfolio
    # and the price of the asset
    ax3 = plt.subplot(413, sharex=ax1)
    perf.loc[:, ['algorithm_period_return', 'price_change']].plot(ax=ax3)
    ax3.legend_.remove()
    ax3.set_ylabel('Percent Change')
    start, end = ax3.get_ylim()
    ax3.yaxis.set_ticks(np.arange(start, end, (end - start) / 5))

    # Fourth chart: Plot our cash
    ax4 = plt.subplot(414, sharex=ax1)
    perf.cash.plot(ax=ax4)
    ax4.set_ylabel('Cash\n({})'.format(quote_currency))
    start, end = ax4.get_ylim()
    ax4.yaxis.set_ticks(np.arange(0, end, end / 5))

    plt.show()
