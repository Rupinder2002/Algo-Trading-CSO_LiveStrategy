# -*- coding: utf-8 -*-
"""
Created on Thu Aug 20 16:07:11 2020

Backtesting Algorithm to be used for zerodha 
Strategy : Backtesting 9:15 open on core ema cso 5 and d-50   
          
Use case: Intraday Trading 

@author: mahadik.prasad
"""

import talib as ta 
import pandas as pd 
import numpy as np 
from datetime import datetime as dt
from datetime import timedelta
from datetime import time
from datetime import date  
import os
import copy 
from kiteconnect import KiteConnect


cwd = os.chdir("D:\Zerodha connect")

#generate trading session
access_token = open("access_token.txt",'r').read()
key_secret = open("api_key.txt",'r').read().split()
kite = KiteConnect(api_key=key_secret[0])
kite.set_access_token(access_token)

instrument_dump = kite.instruments("NSE")
instrument_df = pd.DataFrame(instrument_dump)


def MACD(DF,a,b,c):
    """function to calculate MACD
       typical values a = 12; b =26, c =9"""
    df = DF.copy()
    df["MA_Fast"]=df["Adj Close"].ewm(span=a,min_periods=a).mean()
    df["MA_Slow"]=df["Adj Close"].ewm(span=b,min_periods=b).mean()
    df["MACD"]=df["MA_Fast"]-df["MA_Slow"]
    df["Signal"]=df["MACD"].ewm(span=c,min_periods=c).mean()
    df.dropna(inplace=True)
    return (df["MACD"],df["Signal"])


def instrumentLookup(instrument_df,symbol):
    """Looks up instrument token for a given script from instrument dump"""
    try:
        return instrument_df[instrument_df.tradingsymbol==symbol].instrument_token.values[0]
    except:
        return -1


def fetchOHLC(ticker,interval,duration):
    """extracts historical data and outputs in the form of dataframe"""
    instrument = instrumentLookup(instrument_df,ticker)
    data = pd.DataFrame(kite.historical_data(instrument,dt.now()- timedelta(duration), dt.now(),interval))
    data.set_index("date",inplace=True)
    return data



def ATR(DF,n):
    "function to calculate True Range and Average True Range"
    df = DF.copy()
    df['H-L']=abs(df['high']-df['low'])
    df['H-PC']=abs(df['high']-df['close'].shift(1))
    df['L-PC']=abs(df['low']-df['close'].shift(1))
    df['TR']=df[['H-L','H-PC','L-PC']].max(axis=1,skipna=False)
    df['ATR'] = df['TR'].rolling(n).mean()
    #df['ATR'] = df['TR'].ewm(span=n,adjust=False,min_periods=n).mean()
    df2 = df.drop(['H-L','H-PC','L-PC'],axis=1)
    return df2['ATR']


def CAGR(DF):
    "function to calculate the Cumulative Annual Growth Rate of a trading strategy"
    df = DF.copy()
    df["cum_return"] = (1 + df["ret"]).cumprod()
    n = len(df)/(252*24)
    CAGR = (df["cum_return"].tolist()[-1])**(1/n) - 1
    return CAGR

def volatility(DF):
    "function to calculate annualized volatility of a trading strategy"
    df = DF.copy()
    vol = df["ret"].std() * np.sqrt(252*24)
    return vol

def sharpe(DF,rf):
    "function to calculate sharpe ratio ; rf is the risk free rate"
    df = DF.copy()
    sr = (CAGR(df) - rf)/volatility(df)
    return sr
    

def max_dd(DF):
    "function to calculate max drawdown"
    df = DF.copy()
    df["cum_return"] = (1 + df["ret"]).cumprod()
    df["cum_roll_max"] = df["cum_return"].cummax()
    df["drawdown"] = df["cum_roll_max"] - df["cum_return"]
    df["drawdown_pct"] = df["drawdown"]/df["cum_roll_max"]
    max_dd = df["drawdown_pct"].max()
    return max_dd


def calculate_pos( cap, price): 
    qty = round(cap/price) 
    return qty



tickers = ["RELIANCE"]
#(1+strategy_df["ret"].iloc[-200:]).cumprod().plot()
#tickers = ["HDFCBANK"]
"""
tickers = ["ZEEL","TECHM",
           "TATAMOTORS","SBIN","RELIANCE",
           "NTPC","MARUTI",
           "INDUSINDBK","HDFC",
           "HEROMOTOCO","HDFCBANK",
           "CIPLA","BHARTIARTL","BAJAJFINSV",
           "BAJFINANCE","AXISBANK","ASIANPAINT",
           "PIDILITIND",
           "INDIGO",
           "BANDHANBNK",
           "AUROPHARMA",
           "MUTHOOTFIN","MPHASIS",
           "MANAPPURAM","M&MFIN",
           "HEXAWARE",
           "ERIS",
           "ASTRAL",
           "ALKEM","AJANTPHARM",
           ]
"""
delta = 200
ohlc_intraday = {}
for ticker in tickers:
    ohlc_intraday[ticker] = ohlc = fetchOHLC(ticker,"15minute",delta)

ohlc_dict = copy.deepcopy(ohlc_intraday)


end_a   = time(hour = 15, minute = 0, second = 0)
end_b   = time(hour = 15, minute = 30, second = 0)  
start_a = time(hour = 9, minute = 0, second = 0)
start_b = time(hour = 9, minute = 15, second =0)


tickers_ret = {}
tickers_signal = {}
SL_val = {}
order = pd.DataFrame()
col_names = ["Ticker", "Price", "Buy_Sell", "Date", "Time" ]
pos = pd.DataFrame(columns = col_names)
pos = pos.append([{'Ticker':'Initialization', 'Price':'0', 'Buy_Sell':'None', "Date": 'None', 'Time': 'None'}], ignore_index = True)


#==========================================================================
#ema crossover with vol. spike strategy 
a= 5
b= 50
c= 20 
d= 50
e= 200
spike = 1.5
period = 3
target_pct =6
#brokerage 
br = 100 - 0.03
dd_pct = 0.95
#tgt = 2
r =100
slope_pos = 0.5
slope_neg = -0.5
momentum = 15
for ticker in tickers:
    #dd_pct = round(19/ohlc_dict[ticker]['close'].mean()*100,2)
    print("Appending indicator values for", ticker)
    ohlc_dict[ticker]["EMA" + str(a)] = ohlc_dict[ticker]["close"].ewm(span = a, min_periods = a).mean()
    #ohlc_dict[ticker]["EMAsq" + str(a)] = ohlc_dict[ticker]["EMA" + str(a)].ewm(span = a, min_periods= a).mean()
    #ohlc_dict[ticker]["DEMA" + str(a)] = 2*ohlc_dict[ticker]["EMA" + str(a)] -ohlc_dict[ticker]["EMAsq" + str(a)] 
    ohlc_dict[ticker]["EMA" + str(b)]  = ohlc_dict[ticker]["close"].ewm(span = b, min_periods = b).mean()
    #ohlc_dict[ticker]["EMA" + str(c)]  = ohlc_dict[ticker]["close"].ewm(span = c, min_periods = c).mean()
    #ohlc_dict[ticker]["EMA" + str(d)]  = ohlc_dict[ticker]["close"].ewm(span = d, min_periods = d).mean()
    ohlc_dict[ticker]["EMAsq" + str(b)] = ohlc_dict[ticker]["EMA" + str(b)].ewm(span = b, min_periods= b).mean()
    #ohlc_dict[ticker]["EMAcb" + str(b)] = ohlc_dict[ticker]["EMAsq" + str(b)].ewm(span = b, min_periods= b).mean()
    ohlc_dict[ticker]["DEMA" + str(b)] = 2*ohlc_dict[ticker]["EMA" + str(b)] - 1*ohlc_dict[ticker]["EMAsq" + str(b)]
    #ohlc_dict[ticker]["TEMA" + str(b)] = 3*ohlc_dict[ticker]["EMA" + str(b)] - 3*ohlc_dict[ticker]["EMAsq" + str(b)] +ohlc_dict[ticker]["EMAcb" + str(b)] 
    #ohlc_dict[ticker]["EMA" + str(e)]  = ohlc_dict[ticker]["Adj Close"].ewm(span = e, min_periods = e).mean()
    #ohlc_dict[ticker]["MACD"] = MACD(ohlc_dict[ticker], 12,26,9)[0]
    #ohlc_dict[ticker]["MACD_slope"] = ta.LINEARREG_SLOPE(ohlc_dict[ticker]["MACD"], timeperiod = 5)
    #ohlc_dict[ticker]["Signal"] = MACD(ohlc_dict[ticker], 12,26,9)[1]
    #ohlc_dict[ticker]["Signal_slope"] = ta.LINEARREG_SLOPE(ohlc_dict[ticker]["Signal"], timeperiod = 5)
    #ohlc_dict[ticker]["ATR"] = ATR(ohlc_dict[ticker], 7)
    #ohlc_dict[ticker]["ADX"] = ta.ADX(ohlc_dict[ticker]["high"], ohlc_dict[ticker]["low"], ohlc_dict[ticker]["close"], timeperiod=14)
    #ohlc_dict[ticker]["ADX_slope"] = ta.LINEARREG_SLOPE(ohlc_dict[ticker]["ADX"], timeperiod = 3)
    #ohlc_dict[ticker]["slope"]= ta.LINEARREG_SLOPE(ohlc_dict[ticker]["close"], timeperiod = 2)
    #ohlc_dict[ticker]["roll_mean_vol"] = ohlc_dict[ticker]["Volume"].rolling(period).mean()
    ohlc_dict[ticker].dropna(inplace=True)
    SL_val[ticker] = 0 
    tickers_signal[ticker] = ""
    tickers_ret[ticker] = []
    ohlc_dict[ticker].reset_index(inplace = True)
    ohlc_dict[ticker]['Date'] = pd.to_datetime(ohlc_dict[ticker]['date'], format='%Y:%M:%D').dt.date
    ohlc_dict[ticker]['Time'] = pd.to_datetime(ohlc_dict[ticker]['date'], format='%Y:%M:%D').dt.time
    cso_b=1
    cso_s = 1
     
for ticker in tickers:
    print("Calculating returns for", ticker)
    df = ohlc_dict[ticker]
    tickers_ret[ticker].append(0)
    for i in range(1,len(df)):
        
        if df["Time"][i] == start_b:
             if (df["EMA"+ str(a)][i-1]       >   df["DEMA" + str(b)][i-1] and \
                    cso_b ==1 ):
                    
                    tickers_signal[ticker] = "Buy"
                    pos = pos.append([{'Ticker':ticker,'Price':df["open"][i], "Buy_Sell": "Buy", "Date" : df["Date"][i], "Time" : df["Time"][i]}], ignore_index=True)
                    #place BUY order using API 
                    
                    SL_val[ticker] = (1- dd_pct/100)*df["open"][i]
                    cso_b = 0 
                    cso_s = 1
                    
                    if (df["high"][i]> (1+target_pct/100)*pos[pos.Ticker==ticker]["Price"].iloc[-1]) :
                        tickers_signal[ticker] = ""
                        tickers_ret[ticker].append((((1+target_pct/100)*pos[pos.Ticker==ticker]["Price"].iloc[-1]- df["open"][i])/df["open"][i]))
                        pos = pos.append([{'Ticker':ticker, 'Price':(1+target_pct/100)*pos[pos.Ticker==ticker]["Price"].iloc[-1], 'Buy_Sell':'Sell', "Date" : df["Date"][i], "Time" : df["Time"][i]}], ignore_index = True )
                        #cso_b = 0
                        #cso_s = 1
                    
                    elif(df["low"][i]< SL_val[ticker]) :
                        tickers_signal[ticker] =""
                        tickers_ret[ticker].append(((SL_val[ticker]- df["open"][i])/df["open"][i]))
                        pos = pos.append([{'Ticker':ticker, 'Price':SL_val[ticker], 'Buy_Sell':'Sell', "Date" : df["Date"][i], "Time" : df["Time"][i]}], ignore_index = True )
                     
                    else :
                        tickers_ret[ticker].append(((df["close"][i] - df["open"][i])/df["open"][i]))
                        if df["open"][i] < df["close"][i] and (1-dd_pct/100)*df["close"][i] > SL_val[ticker]: 
                            SL_val[ticker] = (1 -dd_pct/100)*df["close"][i]  
                     
             elif (df["EMA" + str(a)][i-1]       <   df["DEMA" + str(b)][i-1] and \
                      cso_s ==1  ):

                      tickers_signal[ticker] = "Sell"
                      pos = pos.append([{'Ticker':ticker, 'Price':df['open'][i], 'Buy_Sell':'Sell', "Date" : df["Date"][i], "Time" : df["Time"][i]}], ignore_index = True)
                      #place SELL market order using API 
                      
                      SL_val[ticker] = (1+ dd_pct/100)*df["open"][i]
                      cso_b =1
                      cso_s = 0
                      
                      if (df["low"][i]< (1-target_pct/100)*pos[pos.Ticker==ticker]["Price"].iloc[-1]) :
                          tickers_signal[ticker] = ""
                          tickers_ret[ticker].append(-(((1-target_pct/100)*pos[pos.Ticker==ticker]["Price"].iloc[-1]- df["open"][i])/df["open"][i]))
                          pos = pos.append([{'Ticker':ticker, 'Price':(1-target_pct/100)*pos[pos.Ticker==ticker]["Price"].iloc[-1], 'Buy_Sell':'Sell', "Date" : df["Date"][i], "Time" : df["Time"][i]}], ignore_index = True )
                          #cso_b = 1
                          #cso_s = 0
                    
                      elif(df["high"][i]> SL_val[ticker]):  
                          tickers_signal[ticker] =""
                          tickers_ret[ticker].append(-(( SL_val[ticker] - df["open"][i])/df["open"][i]))
                          pos = pos.append([{'Ticker':ticker, 'Price':SL_val[ticker], 'Buy_Sell':'Buy', "Date" : df["Date"][i], "Time" : df["Time"][i]}], ignore_index = True )
                      
                      else:
                          tickers_ret[ticker].append(-((df["close"][i] - df["open"][i])/df["open"][i]))
                          if df["open"][i] < df["close"][i] and (1+dd_pct/100)*df["close"][i] < SL_val[ticker] : 
                              SL_val[ticker] = (1+dd_pct/100)*df["close"][i]
                    
                    
                
        elif df["Time"][i] > start_b and  df["Time"][i] < end_a:
            if tickers_signal[ticker] == "" :
                if (df["EMA"+ str(a)][i-1]       >   df["DEMA" + str(b)][i-1] and \
                    cso_b ==1 ):
                    
                    tickers_signal[ticker] = "Buy"
                    pos = pos.append([{'Ticker':ticker,'Price':df["open"][i], "Buy_Sell": "Buy", "Date" : df["Date"][i], "Time" : df["Time"][i]}], ignore_index=True)
                    #place BUY order using API 
                    
                    SL_val[ticker] = (1- dd_pct/100)*df["open"][i]
                    cso_b = 0 
                    cso_s = 1
                    
                    if (df["high"][i]> (1+target_pct/100)*pos[pos.Ticker==ticker]["Price"].iloc[-1]) :
                        tickers_signal[ticker] = ""
                        tickers_ret[ticker].append((((1+target_pct/100)*pos[pos.Ticker==ticker]["Price"].iloc[-1]- df["open"][i])/df["open"][i]))
                        pos = pos.append([{'Ticker':ticker, 'Price':(1+target_pct/100)*pos[pos.Ticker==ticker]["Price"].iloc[-1], 'Buy_Sell':'Sell', "Date" : df["Date"][i], "Time" : df["Time"][i]}], ignore_index = True )
                        #cso_b = 0
                        #cso_s = 1
                    
                    elif(df["low"][i]< SL_val[ticker]) :
                        tickers_signal[ticker] =""
                        tickers_ret[ticker].append(((SL_val[ticker]- df["open"][i])/df["open"][i]))
                        pos = pos.append([{'Ticker':ticker, 'Price':SL_val[ticker], 'Buy_Sell':'Sell', "Date" : df["Date"][i], "Time" : df["Time"][i]}], ignore_index = True )
                     
                    else :
                        tickers_ret[ticker].append(((df["close"][i] - df["open"][i])/df["open"][i]))
                        if df["open"][i] < df["close"][i] and (1-dd_pct/100)*df["close"][i] > SL_val[ticker]: 
                            SL_val[ticker] = (1 -dd_pct/100)*df["close"][i]  
                     
                elif (df["EMA" + str(a)][i-1]       <   df["DEMA" + str(b)][i-1] and \
                          cso_s ==1  ):
    
                    tickers_signal[ticker] = "Sell"
                    pos = pos.append([{'Ticker':ticker, 'Price':df['open'][i], 'Buy_Sell':'Sell', "Date" : df["Date"][i], "Time" : df["Time"][i]}], ignore_index = True)
                    #place SELL market order using API 
                          
                    SL_val[ticker] = (1+ dd_pct/100)*df["open"][i]
                    cso_b =1
                    cso_s = 0
                          
                    if (df["low"][i]< (1-target_pct/100)*pos[pos.Ticker==ticker]["Price"].iloc[-1]) :
                        tickers_signal[ticker] = ""
                        tickers_ret[ticker].append(-(((1-target_pct/100)*pos[pos.Ticker==ticker]["Price"].iloc[-1]- df["open"][i])/df["open"][i]))
                        pos = pos.append([{'Ticker':ticker, 'Price':(1-target_pct/100)*pos[pos.Ticker==ticker]["Price"].iloc[-1], 'Buy_Sell':'Sell', "Date" : df["Date"][i], "Time" : df["Time"][i]}], ignore_index = True )
                              #cso_b = 1
                              #cso_s = 0
                        
                    elif(df["high"][i]> SL_val[ticker]):  
                        tickers_signal[ticker] =""
                        tickers_ret[ticker].append(-(( SL_val[ticker] - df["open"][i])/df["open"][i]))
                        pos = pos.append([{'Ticker':ticker, 'Price':SL_val[ticker], 'Buy_Sell':'Buy', "Date" : df["Date"][i], "Time" : df["Time"][i]}], ignore_index = True )
                          
                    else:
                        tickers_ret[ticker].append(-((df["close"][i] - df["open"][i])/df["open"][i]))
                        if df["open"][i] < df["close"][i] and (1+dd_pct/100)*df["close"][i] < SL_val[ticker] : 
                            SL_val[ticker] = (1+dd_pct/100)*df["close"][i]
                
                else:
                    tickers_ret[ticker].append(0)
                    
            elif tickers_signal[ticker] == "Buy":
                
                if (df["high"][i]> (1+target_pct/100)*pos[pos.Ticker==ticker]["Price"].iloc[-1]) :
                    tickers_signal[ticker] = ""
                    tickers_ret[ticker].append((((1+target_pct/100)*pos[pos.Ticker==ticker]["Price"].iloc[-1]- df["close"][i-1])/df["close"][i-1]))
                    pos = pos.append([{'Ticker':ticker, 'Price':(1+target_pct/100)*pos[pos.Ticker==ticker]["Price"].iloc[-1], 'Buy_Sell':'Sell', "Date" : df["Date"][i], "Time" : df["Time"][i]}], ignore_index = True )
                    #cso_b = 0
                    #cso_s = 1
                    
                elif(df["low"][i]< SL_val[ticker]) :
                    tickers_signal[ticker] =""
                    tickers_ret[ticker].append(((SL_val[ticker]- df["close"][i-1])/df["close"][i-1]))
                    pos = pos.append([{'Ticker':ticker, 'Price':SL_val[ticker], 'Buy_Sell':'Sell', "Date" : df["Date"][i], "Time" : df["Time"][i]}], ignore_index = True )
                    #cso_b = 0
                    #cso_s = 1
                
                elif (df["EMA" + str(a)][i]      <   df["DEMA" + str(b)][i] ):
                    #and df["close"][i]    >   (1-r/100)*df["DEMA50"][i]  ):
                    tickers_signal[ticker] = "Sell" 
                    tickers_ret[ticker].append(((df["close"][i] - df["close"][i-1])/df["close"][i-1]))
                    pos = pos.append([{'Ticker':ticker, 'Price':df['close'][i], 'Buy_Sell':'Sell', "Date" : df["Date"][i], "Time" : df["Time"][i]}], ignore_index = True )
                    pos = pos.append([{'Ticker':ticker, 'Price':df['close'][i], 'Buy_Sell':'Sell', "Date" : df["Date"][i], "Time" : df["Time"][i]}], ignore_index = True )
                    #Square off the buy order with a market order 
                    SL_val[ticker] = (1+dd_pct/100)*df["close"][i]
                    cso_b = 1
                    cso_s = 0 
                
                #elif (df["EMA" + str(a)][i]      <   df["DEMA" + str(b)][i] ):
                #    tickers_signal[ticker] = "" 
                #    tickers_ret[ticker].append(((df["close"][i] - df["close"][i-1])/df["close"][i-1]))
                #    pos = pos.append([{'Ticker':ticker, 'Price':df['close'][i], 'Buy_Sell':'Sell'}], ignore_index = True )
                    
                else :
                     tickers_ret[ticker].append(((df["close"][i] - df["close"][i-1])/df["close"][i-1]))
                     if df["open"][i] < df["close"][i] and (1-dd_pct/100)*df["close"][i] > SL_val[ticker]: 
                        SL_val[ticker] = (1 -dd_pct/100)*df["close"][i] 
                    
                
                        
            elif tickers_signal[ticker] == "Sell":
                
                if (df["low"][i]< (1-target_pct/100)*pos[pos.Ticker==ticker]["Price"].iloc[-1]) :
                    tickers_signal[ticker] = ""
                    tickers_ret[ticker].append(-(((1-target_pct/100)*pos[pos.Ticker==ticker]["Price"].iloc[-1]- df["close"][i-1])/df["close"][i-1]))
                    pos = pos.append([{'Ticker':ticker, 'Price':(1-target_pct/100)*pos[pos.Ticker==ticker]["Price"].iloc[-1], 'Buy_Sell':'Sell', "Date" : df["Date"][i], "Time" : df["Time"][i]}], ignore_index = True )
                    #cso_b = 1
                    #cso_s = 0
                    
                elif(df["high"][i]> SL_val[ticker]):  
                    tickers_signal[ticker] =""
                    tickers_ret[ticker].append(-(( SL_val[ticker] - df["close"][i-1])/df["close"][i-1]))
                    pos = pos.append([{'Ticker':ticker, 'Price':SL_val[ticker], 'Buy_Sell':'Buy', "Date" : df["Date"][i], "Time" : df["Time"][i]}], ignore_index = True )
                    #cso_b = 1
                    #cso_s = 0
               
                elif (df["EMA" + str(a)][i]      >   df["DEMA" + str(b)][i] ):
                      #and df["close"][i]    <   (1+r/100)*df["DEMA50"][i] ):
                    tickers_signal[ticker] = "Buy"
                    tickers_ret[ticker].append(-((df["close"][i] - df["close"][i-1])/df["close"][i-1]))
                    pos = pos.append([{'Ticker':ticker,'Price':df["close"][i], "Buy_Sell": "Buy", "Date" : df["Date"][i], "Time" : df["Time"][i]}], ignore_index=True)
                    pos = pos.append([{'Ticker':ticker,'Price':df["close"][i], "Buy_Sell": "Buy", "Date" : df["Date"][i], "Time" : df["Time"][i]}], ignore_index=True)
                    #square off the sell order with a market order 
                    SL_val[ticker] = (1-dd_pct/100)*df["close"][i]
                    cso_b = 0
                    cso_s = 1
                
                #elif (df["EMA" + str(a)][i]      >   df["DEMA" + str(b)][i] ):
                #    tickers_signal[ticker] = "" 
                #    tickers_ret[ticker].append(((df["close"][i] - df["close"][i-1])/df["close"][i-1]))
                #    pos = pos.append([{'Ticker':ticker, 'Price':df['close'][i], 'Buy_Sell':'Sell'}], ignore_index = True )
                
                else:
                    tickers_ret[ticker].append(-((df["close"][i] - df["close"][i-1])/df["close"][i-1]))
                    if df["open"][i] > df["close"][i] and (1+dd_pct/100)*df["close"][i] < SL_val[ticker]: 
                        SL_val[ticker] = (1+dd_pct/100)*df["close"][i]
                    
                    
                 
                    
        elif df["Time"][i]== end_a and tickers_signal[ticker]!="":
            
            tickers_signal[ticker] = ""
            if pos["Buy_Sell"].iloc[-1] == "Buy":
                pos = pos.append([{'Ticker':ticker,'Price':df["close"][i],'Buy_Sell':'Sell',"Date" : df["Date"][i], "Time" : df["Time"][i]}], ignore_index = True)
                tickers_ret[ticker].append(((df["close"][i] - df["close"][i-1])/df["close"][i-1]))
                cso_b = 1
                cso_s = 1
            elif pos["Buy_Sell"].iloc[-1] == "Sell":
                pos = pos.append([{'Ticker':ticker,'Price':df["close"][i],'Buy_Sell':'Buy',"Date" : df["Date"][i], "Time" : df["Time"][i]}], ignore_index = True)
                tickers_ret[ticker].append(-((df["close"][i] - df["close"][i-1])/df["close"][i-1]))
                cso_b = 1
                cso_s = 1
        else:
            tickers_ret[ticker].append(0)
            tickers_signal[ticker]= ""
            cso_b = 1
            cso_s = 1
    df["ret"] = np.array(tickers_ret[ticker])
    ohlc_dict[ticker] = df
    ohlc_dict[ticker].set_index(ohlc_dict[ticker]["date"], inplace = True)
    ohlc_dict[ticker].drop(["date"], inplace = True, axis = 1)


strategy_df = pd.DataFrame()
for ticker in tickers:
    strategy_df[ticker] = ohlc_dict[ticker]["ret"]
strategy_df["ret"] = strategy_df.mean(axis=1)
annual_CAGR = CAGR(strategy_df)
sharpe(strategy_df,0.06)
max_ddn = max_dd(strategy_df)  


# vizualization of overall strategy return
#(1+strategy_df["ret"]).cumprod().plot()
 

#visualization of last few days of strategy return 
#rint("Strategy return last few days")
(1+strategy_df["ret"]).cumprod().plot()

#calculating individual stock's KPIs
cagr = {}
sharpe_ratios = {}
max_drawdown = {}
for ticker in tickers:
    print("calculating KPIs for ",ticker)      
    cagr[ticker] =  CAGR(ohlc_dict[ticker])
    sharpe_ratios[ticker] =  sharpe(ohlc_dict[ticker],0.06)
    max_drawdown[ticker] =  max_dd(ohlc_dict[ticker])

KPI_df = pd.DataFrame([cagr,sharpe_ratios,max_drawdown],index=["Return","Sharpe Ratio","Max Drawdown"])      
KPI_df.T


#=============================================================================
#print results and parameters 
print("")
print(tickers)
print("============================ KPIs ==========================")
print('CAGR: ',round(annual_CAGR,2)*100," %")
print('Max_drawdown: ',round(max_ddn,3)*100,' %')
print(round(int(len(pos)/len(tickers))/delta,1),"Settled Trades per ticker per day ")
print("")
#print(dt.now().time())

#Trades today
ohlc_today ={}
for ticker in tickers:
    ohlc_today[ticker] = ohlc_dict[ticker].iloc[-100:]

right = 0 
wrong = 0 
hit_ratio = 0  
i=1  
profit = 0
loss = 0
while i < len(pos)-3:
    if pos["Buy_Sell"][i] =="Buy":
        if pos["Price"][i+1]>pos["Price"][i]:
            right +=1
            profit = profit + pos["Price"][i+1]-pos["Price"][i]
            i+=2
        else:
            wrong+=1
            loss = loss - pos["Price"][i+1]+pos["Price"][i]
            i+=2
    if pos["Buy_Sell"][i] == "Sell":
        if pos["Price"][i+1]<pos["Price"][i]:
            right+=1
            profit = profit - pos["Price"][i+1]+pos["Price"][i]
            i+=2
        else:
            wrong+=1
            loss = loss + pos["Price"][i+1]-pos["Price"][i]
            i+=2
            
hit_ratio = right/(right+wrong)
avg_profit = profit/right
avg_loss = loss/wrong        
print('hit_ratio: ',round(hit_ratio,2))
print('avg_profit: ',round(avg_profit),' points')
print('avg_loss: ',round(avg_loss),' points')

print("risk:reward ", round(avg_loss/avg_profit,2))                        