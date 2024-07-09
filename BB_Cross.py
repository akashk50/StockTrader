import backtrader as bt
import yfinance as yf
import datetime

class BBandsStrategy(bt.Strategy):
    params = (
        ('period', 20),
        ('devfactor', 2),
        ('bb_upper_factor', 0.7),
    )

    def __init__(self):
        self.bbands = {}
        self.pct_b = {}
        self.orders = {}
        
        for i, d in enumerate(self.datas):
            self.bbands[d] = bt.indicators.BollingerBands(
                d.close, period=self.params.period, devfactor=self.params.devfactor)
            self.pct_b[d] = (d.close - self.bbands[d].lines.bot) / (self.bbands[d].lines.top - self.bbands[d].lines.bot)
            self.orders[d] = None  # To keep track of pending orders

    def next(self):
        for i, d in enumerate(self.datas):
            # Check if we have an open order for this data
            if self.orders[d]:
                continue
            
            # Buy condition: Price crosses below the lower Bollinger Band
            if not self.getposition(d):
                if d.close[0] < self.bbands[d].lines.bot[0]:
                    available_cash = self.broker.get_cash()
                    size = int(available_cash / (2*d.close[0]))
                    if size > 0:
                        self.orders[d] = self.buy(data=d, size=size)
            
            # Sell condition: Price reaches 50% of the way to the top Bollinger Band
            elif self.pct_b[d][0] >= self.params.bb_upper_factor:
                self.orders[d] = self.close(data=d)

    def notify_order(self, order):
        if order.status in [order.Completed, order.Canceled, order.Margin]:
            self.orders[order.data] = None

# Initialize Cerebro engine
cerebro = bt.Cerebro()

# Add data feeds to Cerebro
symbols = ["AAPL","META", "GOOG", "AMZN", "NFLX", "TSLA", "JPM"]
for symbol in symbols:
    data = bt.feeds.PandasData(
        dataname=yf.download(tickers=symbol, start='2024-01-01', end='2024-06-19', interval="1d")

    )
    cerebro.adddata(data)

# Add strategy to Cerebro
cerebro.addstrategy(BBandsStrategy)

# Set starting cash
cerebro.broker.set_cash(50000)

# Set broker commission
cerebro.broker.setcommission(commission=0.001)

# Add Analyzer for Sharpe Ratio
cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe_ratio', timeframe=bt.TimeFrame.Days, compression=1)

# Print starting portfolio value
print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
# Run the backtest
results = cerebro.run()

# Print final portfolio value
print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
print('Profit %: ' + str((cerebro.broker.getvalue()/50000 - 1)*100) + '%')

# Get Sharpe Ratio
sharpe_ratio = results[0].analyzers.sharpe_ratio.get_analysis()
print('Sharpe Ratio:', sharpe_ratio)

# Plot the result
cerebro.plot()