# -*- coding: utf-8 -*-
"""
Created on Sat Dec 26 11:19:45 2020

@author: mahadik.prasad
"""

from datetime import datetime as dt
from datetime import timedelta
import pandas as pd 

from sklearn.cluster import KMeans
import numpy as np
from kneed import DataGenerator, KneeLocator
from matplotlib import pyplot as plt
from kiteconnect import KiteConnect
#tickers = ['BAJAJFINSV']
#tickers = [ticker + str(".NS") for ticker in tickers]
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
    #data.drop(data.tail(1).index, inplace = True)
    return data



#ohlc_intraday = {}
#for ticker in tickers:
#    ohlc_intraday[ticker] = yf.download(ticker, start = start,end = end, interval="15m")

df = fetchOHLC("RELIANCE", "15minute", 200)
df['H-L']=abs(df['high']-df['low'])
df['H-PC']=abs(df['high']-df['close'].shift(1))
df['L-PC']=abs(df['low']-df['close'].shift(1))
df['TR']=df[['H-L','H-PC','L-PC']].max(axis=1,skipna=False)
df['TR_pct'] = round(df['TR']/df['close']*100,3)
X = np.array(df['TR_pct'])

#X = np.array(df['close'])
X = np.delete(X,0)

sum_of_squared_distances = []
K = range(1,15)
for k in K:
    km = KMeans(n_clusters=k)
    km = km.fit(X.reshape(-1,1))
    sum_of_squared_distances.append(km.inertia_)
kn = KneeLocator(K, sum_of_squared_distances,S=1.0, curve="convex", direction="decreasing")
kn.plot_knee()
#plt.plot(sum_of_squared_distances)

kmeans = KMeans(n_clusters= kn.knee).fit(X.reshape(-1,1))
c = kmeans.predict(X.reshape(-1,1))
minmax = []
for i in range(kn.knee):
    minmax.append([-np.inf,np.inf])
for i in range(len(X)):
    cluster = c[i]
    if X[i] > minmax[cluster][0]:
        minmax[cluster][0] = X[i]
    if X[i] < minmax[cluster][1]:
        minmax[cluster][1] = X[i]
        
""""
for i in range(len(X)):
    colors = ['b','g','r','c','m','y','k','w']
    c = kmeans.predict(X[i].reshape(-1,1))[0]
    color = colors[c]
    plt.scatter(i,X[i],c = color,s = 1)
for i in range(len(minmax)):
    plt.hlines(minmax[i][0],xmin = 0,xmax = len(X),colors = 'g')
    plt.hlines(minmax[i][1],xmin = 0,xmax = len(X),colors = 'r')
"""    
    