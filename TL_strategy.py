# Strategy Module 
import math
import pandas as pd
import scipy

# Custom modules
import TL_engine as TL_E
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
        
        
class momentum_1_yr(TL_E.Strategy):
    """
    Multi stocks strategy - first alpha
    
    Hypothesis : "Higher past returns are proportional to future return.
    
    INPUT : list_equities = List of ISIN for each equity we need
    """
    
    def __init__(self, equities = list(pd.read_excel("C:/Sauvegarde/Trading_house/Ref_data.xlsx").query("TYPE == 'Common Stock' and COUNTRY == 'FR'")["TICKER"])):
        super().__init__()
        print("Strat initialization ...")
        self.equities = [TL_I.Equity(eq) for eq in equities] # 
        self.tickers = [t.ticker for t in self.equities]

    def activation(self):
        
        self.tmp_data = self.data[self.tickers].iloc[:,[2 * i for i in range(len(self.tickers))]]
        self.tmp_returns = get_return(self.tmp_data).loc[self.current_date]
        self.tmp_df_ranked = self.tmp_returns.rank()
        self.tmp_df_zscored = get_zcoring(self.tmp_df_ranked)
        self.tmp_df_sorted = self.tmp_df_zscored.sort_values()
        
        
        # Buying best at any cost and selling worst.
        buy_list = self.tmp_df_sorted.nlargest()
        sell_list = self.tmp_df_sorted.nsmallest()
        
        
        for t in buy_list.index.get_level_values(0):
            self.buy(t, size = 1)

        for t in sell_list.index.get_level_values(0):
            self.sell(t, size = 1)


        

####################
# Function helper 

def get_return(data:pd.DataFrame):
    return data.ffill().pct_change()
    

####################
# In a way to get alpha factors management we'll use pca engine for risk management mitigation

def get_zcoring(data:pd.DataFrame):
    """
    Zcoring the row for normalisation purpose
    
    """
    
    return (data - data.mean() ) / data.std()
    
    






def fit_pca(returns, nb_factors, svd_solver = 'full'):     
    """
    Fitting PCA model on returns
    
    OUTPUT : 
    PCA model
    
    """

    pca = PCA(n_components = nb_factors, svd_solver = svd_solver)
    pca.fit(returns)
    return pca
        
        
        
        
