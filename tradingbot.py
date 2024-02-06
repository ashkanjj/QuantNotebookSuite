from datetime import datetime
from lumibot.traders import Trader
from lumibot.strategies import Strategy
from lumibot.backtesting import YahooDataBacktesting
from lumibot.brokers import Alpaca
from nicknochnack_finbert_utils import estimate_sentiment

from alpaca_trade_api import REST
from timedelta import Timedelta
# import requests
# import ssl
# ssl._create_default_https_context = ssl._create_unverified_context

# r = requests.get("https://paper-api.alpaca.markets/")

# print(r.status_code)
# print(r.content)

API_KEY = ""

API_SECRET = ""

BASE_URL = "https://paper-api.alpaca.markets"


class TraingStrategy(Strategy):
    def initialize(self, symbol: str, cash_at_risk: float = .5):
        if str == None:
            raise Exception("symbol is not defined")
        self.symbol = symbol
        self.sleeptime = "24H"
        self.last_trade = None
        self.cash_at_risk = cash_at_risk
        self.api = REST(base_url=BASE_URL, key_id=API_KEY,
                        secret_key=API_SECRET)
        pass

    def position_sizing(self):
        cash = self.get_cash()

        last_price = self.get_last_price(self.symbol)

        quantity = round(cash * self.cash_at_risk / last_price, 0)

        return cash, last_price, quantity

    def get_dates(self):
        today = self.get_datetime()
        three_days_prior = today - Timedelta(days=3)
        return today.strftime('%Y-%m-%d'), three_days_prior.strftime('%Y-%m-%d')

    def get_user_sentiment(self):
        today, three_days_prior = self.get_dates()
        news = self.api.get_news(
            symbol=self.symbol, start=three_days_prior, end=today)
        news = [ev.__dict__["_raw"]["headline"] for ev in news]
        probability, sentiment = estimate_sentiment(news)
        return probability, sentiment

    def on_trading_iteration(self):
        cash, last_price, quantity = self.position_sizing()
        print(f"on_trading_iteration {cash}, {quantity}")
        probability, sentiment = self.get_user_sentiment()
        print(probability, sentiment)
        if cash > last_price:
            if sentiment == "positive" and probability > .999:
                if self.last_trade == "sell":
                    self.sell_all()
                order = self.create_order(
                    self.symbol,
                    quantity,
                    "buy",
                    type="bracket",
                    take_profit_price=last_price*1.20,
                    stop_loss_price=last_price*.95
                )
                self.submit_order(order)
                self.last_trade = "buy"
            elif sentiment == "negative" and probability > .999:
                if self.last_trade == "buy":
                    self.sell_all()
                order = self.create_order(
                    self.symbol,
                    quantity,
                    "sell",
                    type="bracket",
                    take_profit_price=last_price*.8,
                    stop_loss_price=last_price*1.05
                )
                self.submit_order(order)
                self.last_trade = "sell"


ALPACA_CONFIG = {
    "API_KEY": API_KEY,
    "API_SECRET": API_SECRET,
    "PAPER": True,
}

start_date = datetime(2020, 1, 1)
end_date = datetime(2023, 12, 31)

broker = Alpaca(ALPACA_CONFIG)
strategy = TraingStrategy(name='mlstrat', broker=broker,
                          parameters={"symbol": "SPY", "cash_at_risk": .5})

strategy.backtest(
    YahooDataBacktesting,
    start_date,
    end_date,
    parameters={"symbol": "SPY", "cash_at_risk": .5}
)
