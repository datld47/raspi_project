import datetime as dt
import pandas as pd

def time_now_to_string():
    return f"{dt.datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"

def copy_attributes(source_obj, target_obj):   
    for (key, value) in source_obj.__dict__.items():
        if key.startswith('_'):
            continue
        target_obj.__setattr__(key, value)
        
def tupple_list_to_list(tuple_list):
    return [ tl[0] for tl in tuple_list]

#Mon, 12 Aug 2024 09:24:53 GMT'
def gmt_date_str_to_datetime(gmt_date_str):
    return dt.datetime.strptime(gmt_date_str, '%a, %d %b %Y %H:%M:%S GMT')

def pd_convert_to_datetime(df, column_name, date_format='%a, %d %b %Y %H:%M:%S GMT'):
    return pd.to_datetime(df[column_name], format=date_format)
    