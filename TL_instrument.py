# Instrument Module 

# Python Module 
import pandas as pd

# Custom module
import TL_datamanagement as TL_D

class Equity():
    """
    Equity Object
    """

    def __init__(self, ticker) :
        self.ticker = ticker

    
    #getter DataFrame of price data
    @property
    def df_data(self):
        print("Getting data price")
        return TL_D.get_historical_data([self.ticker], ["PX_LAST", "PX_OPEN","LOW", 'HIGH'], "20240101", "20240901")
    
    
    #getter last_close
    @property
    def last_close(self):
        print("Getting close price ...")
        return self.df_data[self.ticker]['PX_LAST'].iloc[-1]
    
    #getter DataFrame close price
    @property
    def df_close(self):
        print("Getting close price ...")
        return self.df_data[self.ticker]['PX_LAST']