# Data Management module 
import pandas as pd

# Bloomberg API et stuff
import pdblp
import joblib
from tempfile import mkdtemp

def get_historical_data(tickers, fields, start_date, end_date):
    
    """
    INPUTS : 
     - tickers :: list of ticker - ex : TEP FP EQUITY
     - fields :: list of field
     - start_date :: date format (YYYYMMDD)
     - end_date :: date format (YYYYMMDD)
    
    OUTPUTS :
     - DataFrame :
         index = date
         columns = tickers
         PX_LAST, PX_OPEN, LOW, HIGH per asset
    
    """
   
    frames = []
    con = pdblp.BCon(debug = False, port = 8194, timeout=500000)
    con.start()
    temp_dir = mkdtemp()
    cacher = joblib.Memory(temp_dir)
    bdh = cacher.cache(con.bdh, ignore = ['self'])
    
    for el in tickers:
        frames.append(bdh(el, fields, start_date, end_date))
    
    
    df = pd.concat(frames, axis = 1)
    
    return df
