# -*- coding: utf-8 -*-
"""
Created on Thursday Sept 3 2020

@author: mahadik.prasad
Algorithm to be used for zerodha 
Strategy : EMA cso 5 d-50 early order at 9:15open 
             
          
Use case: Intraday Trading 
Ticker : BAJFINANCE
"""

 
import pandas as pd 
from datetime import datetime as dt
from datetime import timedelta
from datetime import time 
from datetime import date 
import os
from kiteconnect import KiteConnect
import copy 


cwd = os.chdir("D:\Zerodha connect")

#generate trading session
access_token = open("access_token.txt",'r').read()
key_secret = open("api_key.txt",'r').read().split()
kite = KiteConnect(api_key=key_secret[0])
kite.set_access_token(access_token)

instrument_dump = kite.instruments("NSE")
instrument_df = pd.DataFrame(instrument_dump)

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
    #data.set_index("date",inplace=True)
    return data


def placeBOorder(symbol,buy_sell,quantity,sl_price, tgt_price):    
    # Place an intraday stop loss order on NSE
    if buy_sell == "buy":
        t_type=kite.TRANSACTION_TYPE_BUY
        t_type_sl=kite.TRANSACTION_TYPE_SELL
        t_type_tgt= kite.TRANSACTION_TYPE_SELL
    elif buy_sell == "sell":
        t_type=kite.TRANSACTION_TYPE_SELL
        t_type_sl=kite.TRANSACTION_TYPE_BUY
        t_type_tgt= kite.TRANSACTION_TYPE_BUY
    kite.place_order(tradingsymbol=symbol,
                    exchange=kite.EXCHANGE_NSE,
                    transaction_type=t_type,
                    quantity=quantity,
                    order_type=kite.ORDER_TYPE_MARKET,
                    product=kite.PRODUCT_MIS,
                    variety=kite.VARIETY_REGULAR)
    
    kite.place_order(tradingsymbol=symbol,
                    exchange=kite.EXCHANGE_NSE,
                    transaction_type=t_type_sl,
                    quantity=quantity,
                    order_type=kite.ORDER_TYPE_SLM,
                    trigger_price = round(sl_price,1),
                    product=kite.PRODUCT_MIS,
                    variety=kite.VARIETY_REGULAR)
    
    kite.place_order(tradingsymbol=symbol,
                    exchange=kite.EXCHANGE_NSE,
                    transaction_type=t_type_tgt,
                    quantity=quantity,
                    order_type=kite.ORDER_TYPE_LIMIT,
                    price = round(tgt_price,1),
                    product=kite.PRODUCT_MIS,
                    variety=kite.VARIETY_REGULAR)
    
def OnlyBOorder(symbol,buy_sell,quantity,sl_price, tgt_price):    
    # Place an intraday stop loss order on NSE
    if buy_sell == "buy":
        t_type_sl=kite.TRANSACTION_TYPE_SELL
        t_type_tgt= kite.TRANSACTION_TYPE_SELL
    elif buy_sell == "sell":
        t_type_sl=kite.TRANSACTION_TYPE_BUY
        t_type_tgt= kite.TRANSACTION_TYPE_BUY
    
    kite.place_order(tradingsymbol=symbol,
                    exchange=kite.EXCHANGE_NSE,
                    transaction_type=t_type_sl,
                    quantity=quantity,
                    order_type=kite.ORDER_TYPE_SLM,
                    trigger_price = round(sl_price,1),
                    product=kite.PRODUCT_MIS,
                    variety=kite.VARIETY_REGULAR)
    
    kite.place_order(tradingsymbol=symbol,
                    exchange=kite.EXCHANGE_NSE,
                    transaction_type=t_type_tgt,
                    quantity=quantity,
                    order_type=kite.ORDER_TYPE_LIMIT,
                    price = round(tgt_price,1),
                    product=kite.PRODUCT_MIS,
                    variety=kite.VARIETY_REGULAR)

def ModifyOrder(order_id,price, qty):    
    # Modify order given order id
    kite.modify_order(order_id=order_id,
                    trigger_price=round(price,1),
                    quantity = qty, 
                    order_type=kite.ORDER_TYPE_SLM,
                    variety=kite.VARIETY_REGULAR) 
    
def ModifyOrder_Q(order_id, qty):    
    # Modify order given order id
    kite.modify_order(order_id=order_id,
                    quantity = qty, 
                    order_type=kite.ORDER_TYPE_SLM,
                    variety=kite.VARIETY_REGULAR)    
    
def buy_mkt_order(symbol,qty):
    #Place a buy market order on NSE 
    kite.place_order(tradingsymbol=symbol,
                    exchange=kite.EXCHANGE_NSE,
                    transaction_type=kite.TRANSACTION_TYPE_BUY,
                    quantity=qty,
                    order_type=kite.ORDER_TYPE_MARKET,
                    product=kite.PRODUCT_MIS,
                    variety=kite.VARIETY_REGULAR)
    
def sell_mkt_order(symbol, qty):
    #Place a sell market order on NSE 
    kite.place_order(tradingsymbol=symbol,
                    exchange=kite.EXCHANGE_NSE,
                    transaction_type=kite.TRANSACTION_TYPE_SELL,
                    quantity=qty,
                    order_type=kite.ORDER_TYPE_MARKET,
                    product=kite.PRODUCT_MIS,
                    variety=kite.VARIETY_REGULAR)

def cancel_order(ord_id):
    #Cancel the order with given order_id 
    kite.cancel_order(variety=kite.VARIETY_REGULAR,
                      order_id= ord_id )

def main(capital):
    
    a,b = 0,0
    while a < 10:
        try:
            pos_df = pd.DataFrame(kite.positions()["day"])
            break
        except:
            print("can't extract position data..retrying")
            a+=1
    while b < 10:
        try:
            ord_df = pd.DataFrame(kite.orders())
            break
        except:
            print("can't extract order data..retrying")
            b+=1
    global ohlc_dict 
    global param_dict
    global SL_val
    
        
    for ticker in tickers:
        try:
            dd_pct  = param_dict[ticker]["dd_pct"].iloc[0]
            tgt_pct = param_dict[ticker]["tgt_pct"].iloc[0]
            try: 
                SL_val[ticker] = ord_df.loc[(ord_df['tradingsymbol'] ==ticker) & (ord_df['status'].isin(["TRIGGER PENDING"])) & (ord_df["trigger_price"]!=0)]["trigger_price"].values[-1]
            except Exception as e:
                    print(e)
    
            ohlc_dict[ticker] = copy.deepcopy(fetchOHLC(ticker,"15minute",200))
            print("Looping for", ticker)
            ohlc_dict[ticker]["EMA5"]            =   ohlc_dict[ticker]["close"].ewm(span = 5, min_periods = 5).mean()
            #ohlc_dict[ticker]["EMA5sq"]         =   ohlc_dict[ticker]["EMA5"].ewm(span = 5, min_periods= 5).mean()
            #ohlc_dict[ticker]["DEMA5"]          =   2*ohlc_dict[ticker]["EMA5"] -ohlc_dict[ticker]["EMA5sq"]  
            ohlc_dict[ticker]["EMA50"]           =   ohlc_dict[ticker]["close"].ewm(span = 50, min_periods = 50).mean()
            ohlc_dict[ticker]["EMA50sq"]         =   ohlc_dict[ticker]["EMA50"].ewm(span = 50, min_periods= 50).mean()
            ohlc_dict[ticker]["DEMA50"]          =   2*ohlc_dict[ticker]["EMA50"] -ohlc_dict[ticker]["EMA50sq"]   
            
            
            ohlc_dict[ticker].dropna(inplace=True)
            temp = ohlc_dict[ticker].tail(1)
            ohlc_dict[ticker].drop(ohlc_dict[ticker].tail(1).index, inplace = True)
            ohlc_dict[ticker]['Date'] = pd.to_datetime(ohlc_dict[ticker]['date'], format='%Y-%M-%D').dt.date
            ohlc_dict[ticker]['Time'] = pd.to_datetime(ohlc_dict[ticker]['date'], format='%Y:%M:%D').dt.time

            
            df = ohlc_dict[ticker]
            
            print(df.tail(2))
            print(dt.now().time())
            
            #incomplete last candle is loaded once in the dataframe 
            #it is the last row of the dataframe
            if df["Time"].iloc[-1] == time(hour = 15, minute = 15, second = 0): 
                quantity = int(capital/temp["open"].iloc[-1]) 
                print(temp)
                if (df["EMA5"].iloc[-1]             >   df["DEMA50"].iloc[-1]    and     cso_b[ticker] == 1 ) :
                        
                    SL_val[ticker] = (1-dd_pct/100)*temp["close"].iloc[-1]
                    placeBOorder(ticker,"buy",quantity, (1-dd_pct/100)*temp["close"].iloc[-1], (1+tgt_pct/100)*temp["close"].iloc[-1])
                    print("Early BO long order placed for", ticker)
                    cso_b[ticker] = 0
                    cso_s[ticker] = 1
                    
                elif (df["EMA5"].iloc[-1]           <   df["DEMA50"].iloc[-1]    and     cso_s[ticker] == 1 ):
                        
                    SL_val[ticker] = (1+dd_pct/100)*temp["close"].iloc[-1]
                    placeBOorder(ticker,"sell",quantity,(1+dd_pct/100)*temp["close"].iloc[-1], (1-tgt_pct/100)*temp["close"].iloc[-1])
                    print("Early BO short order placed for", ticker)
                    cso_b[ticker] = 1
                    cso_s[ticker] = 0
                
            elif df["Time"].iloc[-1] >= time(hour = 9, minute = 15, second =0) and  df["Time"].iloc[-1] < time(hour = 15, minute = 0, second = 0):
                quantity = int(capital/df["close"].iloc[-1])
                
                if len(pos_df.columns)==0:
                    
                    if (df["EMA5"].iloc[-1]             >   df["DEMA50"].iloc[-1]    and     cso_b[ticker] == 1 ) :
                        
                        SL_val[ticker] = (1-dd_pct/100)*df["close"].iloc[-1]
                        placeBOorder(ticker,"buy",quantity, (1-dd_pct/100)*df["close"].iloc[-1], (1+tgt_pct/100)*df["close"].iloc[-1])
                        print("BO long order placed for", ticker)
                        cso_b[ticker]  = 0
                        cso_s[ticker] = 1
                    
                    elif (df["EMA5"].iloc[-1]           <   df["DEMA50"].iloc[-1]    and     cso_s[ticker] == 1 ):
                        
                        SL_val[ticker] = (1+dd_pct/100)*df["close"].iloc[-1]
                        placeBOorder(ticker,"sell",quantity,(1+dd_pct/100)*df["close"].iloc[-1], (1-tgt_pct/100)*df["close"].iloc[-1])
                        print("BO short order placed for", ticker)
                        cso_b[ticker]  = 1
                        cso_s[ticker] = 0
                
                elif len(pos_df.columns)!=0 and ticker not in pos_df["tradingsymbol"].tolist():
                    
                    if (df["EMA5"].iloc[-1]             >   df["DEMA50"].iloc[-1]    and     cso_b[ticker] == 1 ) :
                        
                        SL_val[ticker] = (1-dd_pct/100)*df["close"].iloc[-1]
                        placeBOorder(ticker,"buy",quantity, (1-dd_pct/100)*df["close"].iloc[-1], (1+tgt_pct/100)*df["close"].iloc[-1])
                        print("Category 2 BO long order placed for", ticker)
                        cso_b[ticker]  = 0
                        cso_s[ticker] = 1
                    
                    elif (df["EMA5"].iloc[-1]           <   df["DEMA50"].iloc[-1]    and     cso_s[ticker] == 1 ):
                        
                        SL_val[ticker] = (1+dd_pct/100)*df["close"].iloc[-1]
                        placeBOorder(ticker,"sell",quantity,(1+dd_pct/100)*df["close"].iloc[-1], (1-tgt_pct/100)*df["close"].iloc[-1])
                        print("Category 2 BO short order placed for", ticker)
                        cso_b[ticker]  = 1
                        cso_s[ticker] = 0
                
                elif len(pos_df.columns)!=0 and ticker in pos_df["tradingsymbol"].tolist():
                    
                    if pos_df[pos_df["tradingsymbol"]== ticker]["quantity"].values[0] == 0:
                        try:
                            order_ids = ord_df.loc[(ord_df['tradingsymbol'] == ticker) & (ord_df['status'].isin(["TRIGGER PENDING", "OPEN"]))]["order_id"].to_list()
                            for order_id in order_ids:
                                cancel_order(order_id)
                        except Exception as e:
                            print(e)
                                 
                        if (df["EMA5"].iloc[-1]             >   df["DEMA50"].iloc[-1]    and     cso_b[ticker] == 1 ) :
                        
                            SL_val[ticker] = (1-dd_pct/100)*df["close"].iloc[-1]
                            placeBOorder(ticker,"buy",quantity, (1-dd_pct/100)*df["close"].iloc[-1], (1+tgt_pct/100)*df["close"].iloc[-1])
                            print("Category 2 BO long order placed for", ticker)
                            cso_b[ticker]  = 0
                            cso_s[ticker] = 1
                    
                        elif (df["EMA5"].iloc[-1]           <   df["DEMA50"].iloc[-1]    and     cso_s[ticker] == 1 ):
                        
                            SL_val[ticker] = (1+dd_pct/100)*df["close"].iloc[-1]
                            placeBOorder(ticker,"sell",quantity,(1+dd_pct/100)*df["close"].iloc[-1], (1-tgt_pct/100)*df["close"].iloc[-1])
                            print("Category 2 BO short order placed for", ticker)
                            cso_b[ticker]  = 1
                            cso_s[ticker] = 0
                    
                    elif pos_df[pos_df["tradingsymbol"]==ticker]["quantity"].values[0] > 0:
                        
                        cso_b[ticker] =0
                        quantity = abs(pos_df[pos_df["tradingsymbol"]==ticker]["quantity"].values[0])
                        if (df["EMA5"].iloc[-1]         <   df["DEMA50"].iloc[-1]):
                            sell_mkt_order(ticker, 2*quantity) 
                            order_ids = ord_df.loc[(ord_df['tradingsymbol'] == ticker) & (ord_df['status'].isin(["TRIGGER PENDING", "OPEN"]))]["order_id"].to_list()
                            for order_id in order_ids:
                                cancel_order(order_id)
                            OnlyBOorder(ticker,"sell",quantity,(1+dd_pct/100)*df["close"].iloc[-1], (1-tgt_pct/100)*df["close"].iloc[-1])
                            print("Long => Short Reverse position for", ticker)
                            SL_val[ticker] = (1+dd_pct/100)*df["close"].iloc[-1]
                            cso_b[ticker]  = 1
                            cso_s[ticker]  = 0
                        
                        else:
                            #modify the stop Loss if its a green candle 
                            if (df["close"].iloc[-1]  >   df["open"].iloc[-1]) and ((1-dd_pct/100)*df["close"].iloc[-1] > SL_val[ticker] ):
                                order_id = ord_df.loc[(ord_df['tradingsymbol'] == ticker) & (ord_df['status'].isin(["TRIGGER PENDING"])) & (ord_df['trigger_price'] < df["close"].iloc[-1])]["order_id"].values[0]
                                ModifyOrder(order_id,(1-dd_pct/100)*df["close"].iloc[-1], quantity)
                                print("SL modified for",ticker )
                            else:
                                order_id = ord_df.loc[(ord_df['tradingsymbol'] == ticker) & (ord_df['status'].isin(["TRIGGER PENDING"])) & (ord_df['trigger_price'] < df["close"].iloc[-1])]["order_id"].values[0]
                                ModifyOrder_Q(order_id, abs(pos_df[pos_df["tradingsymbol"]==ticker]["quantity"].values[0]))
                                print("Quantity check done on SL for", ticker)
                    
                    elif pos_df[pos_df["tradingsymbol"]==ticker]["quantity"].values[0] < 0:
                        
                        cso_s[ticker] = 0
                        quantity = abs(pos_df[pos_df["tradingsymbol"]==ticker]["quantity"].values[0])
                        if (df["EMA5"].iloc[-1]         >   df["DEMA50"].iloc[-1]):
                            buy_mkt_order(ticker, 2*quantity)
                            order_ids = ord_df.loc[(ord_df['tradingsymbol'] == ticker) & (ord_df['status'].isin(["TRIGGER PENDING", "OPEN"]))]["order_id"].to_list()
                            for order_id in order_ids:
                                cancel_order(order_id)
                            OnlyBOorder(ticker,"buy",quantity, (1-dd_pct/100)*df["close"].iloc[-1], (1+tgt_pct/100)*df["close"].iloc[-1])
                            print("Short => Long Reverse position for", ticker)
                            SL_val[ticker] = (1-dd_pct/100)*df["close"].iloc[-1]
                            cso_b[ticker]  = 0
                            cso_s[ticker]  = 1
                        
                        else:    
                            #modify the stop loss if its a red candle
                            if (df["open"].iloc[-1]  >   df["close"].iloc[-1]) and ((1+dd_pct/100)*df["close"].iloc[-1] < SL_val[ticker]):
                                order_id = ord_df.loc[(ord_df['tradingsymbol'] == ticker) & (ord_df['status'].isin(["TRIGGER PENDING"])) & (ord_df['trigger_price'] > df["close"].iloc[-1])]["order_id"].values[0]
                                ModifyOrder(order_id, (1+dd_pct/100)*df["close"].iloc[-1], quantity)
                                print("SL modified for", ticker)
                            else:
                                order_id = ord_df.loc[(ord_df['tradingsymbol'] == ticker) & (ord_df['status'].isin(["TRIGGER PENDING"])) & (ord_df['trigger_price'] > df["close"].iloc[-1])]["order_id"].values[0]
                                ModifyOrder_Q(order_id, quantity)
                                print("Quantity check done on SL for", ticker)
                                
            elif df["Time"].iloc[-1]== time(hour = 15, minute = 0, second = 0) :

                if ticker in pos_df["tradingsymbol"].tolist() and pos_df[pos_df["tradingsymbol"]==ticker]["quantity"].values[0] > 0:
                    sell_mkt_order(ticker, abs(pos_df[pos_df["tradingsymbol"]== ticker]["quantity"].values[0])) 
                    order_ids = ord_df.loc[(ord_df['tradingsymbol'] == ticker) & (ord_df['status'].isin(["TRIGGER PENDING", "OPEN"]))]["order_id"].to_list()
                    for order_id in order_ids:
                        cancel_order(order_id)
                    print("Exit position for", ticker)
                
                elif ticker in pos_df["tradingsymbol"].tolist() and pos_df[pos_df["tradingsymbol"]==ticker]["quantity"].values[0] < 0:
                    buy_mkt_order(ticker,abs(pos_df[pos_df["tradingsymbol"]==ticker]["quantity"].values[0])) 
                    order_ids = ord_df.loc[(ord_df['tradingsymbol'] == ticker) & (ord_df['status'].isin(["TRIGGER PENDING", "OPEN"]))]["order_id"].to_list()
                    for order_id in order_ids:
                        cancel_order(order_id)
                    print("Exit position for", ticker)
                    
            #ohlc_dict[ticker] = df
            #ohlc_dict[ticker].set_index(ohlc_dict[ticker]["Datetime"], inplace = True)
            #ohlc_dict[ticker].drop(["Datetime"], inplace = True, axis = 1)
        
        except Exception as e:
            print("API error for ticker :",ticker)
            print(e)
            
       
#=============================================================================
#enter capital INR
capital = 1
param = ["dd_pct", "tgt_pct" ]

tickers =["RELIANCE"]
#tickers =["BAJAJFINSV", "ZEEL"]
param_dict = {}
SL_val = {}
cso_b = {}
cso_s = {}

for ticker in tickers:
    param_dict[ticker] = pd.DataFrame(columns = param)
    SL_val[ticker] = 0
    #cso_b/cso_s are flags used to prevent re entering a closed position in a Crossover
    cso_b[ticker] = 1 
    cso_s[ticker] = 1

#intialize ticker parameters    
#param_dict["BAJAJFINSV"] = param_dict["BAJAJFINSV"].append({'dd_pct': 6, 'tgt_pct': 6.5 }, ignore_index = True)
param_dict["RELIANCE"] = param_dict["RELIANCE"].append({'dd_pct': 0.95 , 'tgt_pct': 6 }, ignore_index = True)

ohlc_dict = {}

#=============================================================================

st = time(hour = 9, minute =15, second = 1)
first_run =1 

while True:
    
    if dt.now().time().hour == st.hour and dt.now().time().minute == st.minute and dt.now().time().second == st.second :
        
        try:
            main(capital)
            #print("Hi", dt.now().time())
            if first_run ==1:
                st = (dt.combine(date.today(), st) + timedelta(minutes=15, seconds = 1)).time()
            else: 
                st = (dt.combine(date.today(), st) + timedelta(minutes=15)).time()
            first_run = 0
            
        except KeyboardInterrupt: 
            print('\n\nKeyboard exception received. Exiting.')
            exit()
       
