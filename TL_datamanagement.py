# Data Management module 

# Bloomberg API et stuff
import pdblp
import joblib
from tempfile import mkdtemp

def get_historical_data(tickers, fields, start_date, end_date):
    
    """
    INPUTS : 
     - tickers :: list of ticker - ex : /isin/ + isin code
     - fields :: list of field
     - start_date :: date format (YYYYMMDD)
     - end_date :: date format (YYYYMMDD)
    
    OUTPUTS :
     - DataFrame :
         index = date
         columns = tickers
         PX_LAST, PX_OPEN, LOW, HIGH per asset
    
    """
    
    tickers_isin = ['/isin/' + str(t) for t in tickers]
    
    con = pdblp.BCon(debug = False, port = 8194, timeout=500000)
    con.start()
    temp_dir = mkdtemp()
    cacher = joblib.Memory(temp_dir)
    bdh = cacher.cache(con.bdh, ignore = ['self'])
    
    df = bdh(tickers_isin, fields, start_date, end_date)
    
    # Renaming DataFrame columns for better visualisation
    col_dict = {}
    for i,j in zip(tickers, tickers_isin):
        col_dict[j] = i
    
    df = df.rename(columns=col_dict)
    
    return df