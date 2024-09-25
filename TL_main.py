# Main module of my e-trading environment

import pandas as pd
import matplotlib.pyplot as plt
import TL_engine as TL_E
import TL_strategy as TL_S
import TL_datamanagement as TL_D


if __name__ == "__main__" :
    
    #df = TL_D.get_historical_data(["US0378331005", "US67066G1040"], ["PX_LAST", "PX_OPEN","LOW", 'HIGH'], "20240101", "20240901")
    
    
    # Create strategy
    universe = list(pd.read_excel("C:/Sauvegarde/Trading_house/Ref_data.xlsx")["TICKER"]) # Liste de l'univers investissable
    data = TL_D.get_historical_data(universe, ["PX_LAST", "PX_OPEN"], start_date = "20240101", end_date = "20240901")
    engine = TL_E.Engine(data, cash_init = 1000000) 
    df = engine.data
    
    #s = df[t].iloc[:,[2 * i for i in range(len(t))]]
    
    engine.add_strategy(TL_S.momentum_1_yr())
    engine.run()
    
    engine.portfolio.NAV_series
    engine.portfolio.cash_series
    df = engine.summary()
    df['bench'] = (1+engine.data["CAC Index"]["PX_LAST"].ffill().pct_change())*1000000
    df[['total_aum','bench']].plot()

    plt.plot()
    plt.legend()
    plt.show()

    engine.get_stats()
