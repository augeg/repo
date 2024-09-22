# Library for personal e-trading

# Importing major python module 
import pandas as pd
import numpy as np

# import seaborn as sns
import matplotlib.pyplot as plt

from tqdm import tqdm

# Custom module
import TL_instrument as TL_I
import TL_datamanagement as TL_D

class Engine():
    """
    Main engine - used for running the backtest process
    """
    
    def __init__(self, cash_init = 1000):
        self.strategy = None
        self.cash = cash_init
        self.universe = list(pd.read_excel("C:/Sauvegarde/Trading_house/ISIN_LIST.xlsx").iloc[:,0]) # Liste de l'univers investissable
        self.data = TL_D.get_historical_data(self.universe, ["PX_LAST", "PX_OPEN","LOW", 'HIGH'], "20240101", "20240901")
        self.current_date = None
        self.portfolio = Portfolio()
        self.NAV = 0
        self.initial_cash = cash_init
    
    def summary(self)                    :
        # Create a dataframe with the cash and stock holdings at the end of each bar
        df = pd.DataFrame({'stock':self.portfolio.NAV_series, 'cash':self.portfolio.cash_series}).fillna(method='bfill')
        df['total_aum'] = df['stock'] + df['cash']
        return df  
    
    def plot(self):
        df = self.summary()
        plt.plot(df['total_aum'],label='Strategy')
        plt.legend()
        plt.show()

    def add_portfolio(self, ptf):
        self.portfolio = ptf
    
    def add_strategy(self, strategy):
        self.strategy = strategy
        
    def run(self):
        
        for _date in tqdm(self.data.index):
            self.current_date = _date
            self.strategy.current_date = self.current_date
            self.strategy.add_data(self.data)
            self.strategy.add_cash(self.cash)
            self.strategy.activation()
            self.fill_orders()
            self.update_portfolio(_date)
            self.portfolio.cash_series[_date] = self.cash
            self.portfolio.NAV_series[_date] = self.NAV
    
    def update_portfolio(self, _date):
        
        #Updating price
        for pos in self.portfolio.positions : 
            ticker = pos.ticker
            tmp_price = self.data.loc[_date][ticker]['PX_LAST']
            pos.update_price(tmp_price)
                    
            # Calculating NAV portfolio after update        
            pos.NAV = pos.nominal * pos.price
                
    
        # Calculating NAV portfolio after update        
        self.NAV = sum([el.NAV for el in self.portfolio.positions])        
        
   
    
    def fill_orders(self):
        
        """
        this function create buy and sell order based on condition
         - Buy order need cash balance
         - No Short Selling at the moment - need share to complete order
        
        """
        
        for order in self.strategy.orders:   
            # A strategy can have n orders
            
            fill_price = self.data.loc[self.current_date][order.ticker]['PX_OPEN']
            can_fill = False

            if order.side == 'buy' and self.cash >= self.data.loc[self.current_date][order.ticker]['PX_OPEN'] * order.size:
                if order.type == 'limit':
                
                # LIMIT BUY ORDERS ONLY GET FILLED IF THE LIMIT PRICE IS GREATER THAN OR EQUAL TO THE LOW PRICE
                    if order.limit_price >= self.data.loc[self.current_date][order.ticker]['LOW']:
                        fill_price = order.limit_price
                        can_fill = True
                        print(self.current_date, 'Buy Filled. ', "limit",order.limit_price," / low", self.data.loc[self.current_date][order.ticker]['LOW'])
                    else :
                        print(self.current_date,'Buy NOT filled. ', "limit",order.limit_price," / low", self.data.loc[self.current_date][order.ticker]['LOW'])
                else :
                    can_fill = True
                    
            elif order.side == 'sell' and self.strategy.position_size >= order.size:
                if order.type == 'limit':
                #LIMIT SELL ORDERS ONLY GET FILLED IF THE LIMIT PRICE IS LESS THAN OR EQUAL TO THE HIGH PRICE
                
                    if order.limit_price <= self.data.loc[self.current_date][order.ticker]['HIGH']:
                        fill_price = order.limit_price
                        can_fill = True
                        print(self.current_date,'Sell filled. ', "limit",order.limit_price," / high", self.data.loc[self.current_date][order.ticker]['HIGH'])
                    else:
                        print(self.current_date,'Sell NOT filled. ', "limit",order.limit_price," / high", self.data.loc[self.current_date][order.ticker]['HIGH'])
                
                else:
                    can_fill = True
                           
            if can_fill:
                t = Trade(
                    
                    ticker = order.ticker,
                    side = order.side,
                    price = fill_price,
                    size = order.size,
                    type = order.type,
                    idx = self.current_date)
    
                self.strategy.trades.append(t)
                self.cash -= t.price * t.size
                
                print("filling portfolio with positions ...")
                p = Position(
                    t.ticker,
                    t.size,
                    t.price,
                    t.type,
                    t.idx)

                
                self.portfolio.add_or_update_position(p)
        
        print(self.portfolio.positions)
        
        
        # Reinitialization when orders are completed - or not filled
        self.strategy.orders = []
   
    
    
    def get_stats(self):
        
        metrics = {}
        
        # Starting from now, my benchmark is a buy and hold portfolio holding CAC INDEX
        df = self.summary()
        
        # Total return of the strategy
        total_return = df.iloc[-1,2] / self.initial_cash - 1
        metrics['total_return'] = total_return

        # Caclulate the total exposure to the asset as a percentage of our total holdings
        metrics['exposure_pct'] = ((df['stock'] / df['total_aum']) * 100).mean()

        # Calculate annualized returns
        p = df.total_aum
        metrics['returns_annualized'] = ((p.iloc[-1] / p.iloc[0]) ** (1 / ((p.index[-1] - p.index[0]).days / 365)) - 1) * 100
        
        # Calculate the annualized volatility. I'm assuming that we're using daily data of an asset that trades only during working days (ie: stocks)
        # If you're  trading cryptos, use 365 instead of 252
        self.trading_days = 252
        metrics['volatility_ann'] = p.pct_change().std() * np.sqrt(self.trading_days) * 100
       
        
        # Now that we have the annualized returns and volatility, we can calculate the Sharpe Ratio
        # Keep in mind that the sharpe ratio also requires the risk free rate. For simplicity, I'm assuming a risk free rate of 0.as_integer_ratio
        # You should define the risk_free_rate in the __init__() method instead of here.
        self.risk_free_rate = 0
        metrics['sharpe_ratio'] = (metrics['returns_annualized'] - self.risk_free_rate) / metrics['volatility_ann']
        
        # Max drawdown
        metrics['max_drawdown'] = get_max_drawdown(p)


        return metrics
    
    def plot(self):
        plt.plot(self.portfolio['total_aum'],label='Strategy')
        plt.show()        
    
class Strategy():
    """
    Execution engine of trading strategies
    
    """
    
    def __init__(self):
        self.current_date = None
        self.cash = None
        self.orders = []
        self.trades = []
        self.tickers = []
        
    def buy_limit(self,ticker,limit_price, size=1):
        self.orders.append(
            Order(
                ticker = ticker,
                side = 'buy',
                size = size,
                limit_price=limit_price,
                order_type='limit',
                idx = self.current_date
            ))
        
    def sell_limit(self,ticker,limit_price, size=1):
        self.orders.append(
            Order(
                ticker = ticker,
                side = 'sell',
                size = -size,
                limit_price=limit_price,
                order_type='limit',
                idx = self.current_date
            ))
    
    def buy(self, ticker, size = 1):
        self.orders.append(
            Order(
                ticker = ticker,
                side = 'buy',
                size = size,
                idx = self.current_date
                ))
    
    def sell(self, ticker, size = 1):
        self.orders.append(
            Order(
                ticker = ticker,
                side = 'sell',
                size = size,
                idx = self.current_date
                ))

    @property
    def position_size(self):
        print("Getting position size ... ")
        return sum([t.size for t in self.trades])

    def add_cash(self, cash_init:int):
        self.cash = cash_init
    
    def add_data(self, df:pd.DataFrame):
        if self.tickers :
            self.data = df[self.tickers]
        else :
            self.data = df
    
class Trade():
    """
    
    Trade object engine
    
    """
    
    def __init__(self, ticker,side,size,price,type,idx):
        self.ticker = ticker
        self.side = side
        self.price = price
        self.size = size
        self.type = type
        self.idx = idx
    
    def __repr__(self):
        """
        Better describing of our trades
        
        Returns
        -------
        str
            DESCRIPTION.

        """
        return f'<Trade: {self.idx} {self.ticker} {self.size}@{self.price}>'
    
 
    
class Order(TL_I.Equity):
    """
    Buy or sell order - when order is filled it ll create a trade object
    
    """
    
    def __init__(self, ticker, size, side, idx, limit_price=None, order_type='market'):
        super().__init__(ticker)
        self.side = side
        self.size = size
        self.idx = idx
        self.type = order_type
        self.limit_price = limit_price

        @property
        def ticker(self):
            print("Getting ticker")
            return self.instrument.ticker



class Position():
    """
    
    Position object engine
    
    """
    
    def __init__(self, ticker,amount,price,type,idx):
        self.ticker = ticker
        self.price = price
        self.idx = idx
        self.type = -1 if type == 'sell' else 1
        self.nominal = self.type * amount
        self.NAV = self.nominal * self.price
    
    def update_date(self, new_date):
        self.idx = new_date
        
    def update_nominal(self, new_nominal):
        self.nominal += new_nominal    
        self.NAV = self.nominal * self.price
        
    def update_price(self, new_price):
        self.price = new_price
        self.NAV = self.nominal * self.price
    
    def __repr__(self):
        """
        Better describing of our Position
        
        Returns
        -------
        str
            DESCRIPTION.

        """
        return f'<Position: {self.idx} {self.ticker} {self.nominal}@{self.price}>'





class Portfolio():
    
    """
    Portfolio class which will contain total position for each asset at each time period
    also contains cash balance
    """

    def __init__(self, name = 'GA', cash = 1000):
        self.trades = [] # List of trades
        self.positions = [] # List of positions
        self.strategies = [] # List of strategy
        self.cash = cash
        self.name = name
        self.cash_series = {}
        self.NAV_series = {}
        
    def add_or_update_position(self, p):
        update = False
        for pos in self.positions :
            if p.ticker == pos.ticker :
            # update :
                pos.update_date(p.idx)
                pos.update_nominal(p.nominal)
                pos.update_price(p.price)
                
                if pos.nominal == 0 :
                    print("Closing positions ...")
                    self.positions.remove(pos)
                else :
                    print("Updating positions ...")
                
                update = True
        
        if update == False :
            print("Adding new positions ...")
            self.positions.append(p)
        

        
        self.cash -= p.nominal * p.price

    def add_trade(self, t):
        self.trades.append(t)
        
    def add_strategy(self, s):
        self.strategies.append(s)
        
    @property
    def get_NAV(self):
        print("Getting portfolio NAV ... ")
        return self.cash + sum([p.NAV for p in self.positions])




def get_max_drawdown(close):
    roll_max = close.cummax()
    daily_drawdown = close / roll_max - 1.0
    max_daily_drawdown = daily_drawdown.cummin()
    return max_daily_drawdown.min() * 100        
        
    
    
    
    
