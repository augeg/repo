# Main module of my e-trading environment

import pandas as pd
import matplotlib.pyplot as plt
import math

# Custom module
import TL_engine as TL_E
import TL_datamanagement as TL_D
import TL_instrument as TL_I


class BuyAndSellSwitch(TL_E.Strategy):
    
    """
    At first we only deal a 1 ticker strategy and then we'll adapt to many. Each strategy must have the same format
    
    INPUT : list_equities = List of ISIN for each equity we need
    """
    def __init__(self, equities):
        super().__init__()
        print("Strat initialization ...")
        self.equities = [TL_I.Equity(eq) for eq in equities] # 
        self.tickers = [t.ticker for t in self.equities]
        
        # other stuff specific to the current strategy
        
        
    def activation(self):
        print(self.position_size)  
        
        
        if self.position_size == 0:
            # Buy Side :
            limit_price = self.data[self.tickers[0]]['PX_OPEN'].mean() * 0.995
            
            # Order :
            self.buy_limit(self.tickers[0], size=1, limit_price=limit_price)
            
            print(self.current_date,"buy")
        else:
            
            # Sell Side :
            limit_price = self.data[self.tickers[0]]['PX_OPEN'].mean() * 1.005
            
            # Order :
            self.sell_limit(self.tickers[0], size=1,limit_price=limit_price)
            print(self.current_date,"sell")
    
class SMACrossover(TL_E.Strategy):
    """
    At first we only deal a 1 ticker strategy and then we'll adapt to many. Each strategy must have the same format
    
    INPUT : list_equities = List of ISIN for each equity we need
    """
    def __init__(self, equities):
        super().__init__()
        print("Strat initialization ...")
        self.equities = [TL_I.Equity(eq) for eq in equities] # 
        self.tickers = [t.ticker for t in self.equities]
        
        # other stuff specific to the current strategy

        
    def activation(self):
        self.tmp_data = self.data[self.tickers[0]]
        self.tmp_data['sma12'] = self.data[self.tickers[0]]['PX_LAST'].rolling(12).mean()
        self.tmp_data['sma24'] = self.data[self.tickers[0]]['PX_LAST'].rolling(24).mean()
        
        if self.position_size == 0:
            
            if self.tmp_data['sma12'].loc[self.current_date] > self.tmp_data['sma24'].loc[self.current_date] :

                limit_price = self.tmp_data['PX_LAST'].loc[self.current_date] * 0.995
                
                order_size = math.floor(self.cash / limit_price)
                
                self.buy_limit(self.tickers[0], size=order_size, limit_price=limit_price)
                
        elif self.tmp_data['sma12'].loc[self.current_date] < self.tmp_data['sma24'].loc[self.current_date] :
            
            limit_price = self.tmp_data['PX_LAST'].loc[self.current_date] * 1.005
            
            self.sell_limit(self.tickers[0], size=self.position_size, limit_price=limit_price)
              
        else :
            pass

if __name__ == "__main__" :
    
    #df = TL_D.get_historical_data(["US0378331005", "US67066G1040"], ["PX_LAST", "PX_OPEN","LOW", 'HIGH'], "20240101", "20240901")
    
    
    # Create strategy
    engine = TL_E.Engine()       
    engine.add_strategy(SMACrossover(["US0378331005", "US67066G1040"]))
    engine.run()
    
    df = engine.summary()
    plt.plot(df['total_aum'],label='Strategy')
    plt.legend()
    plt.show()

    engine.get_stats()