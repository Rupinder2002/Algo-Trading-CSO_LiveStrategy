# Algo-Trading-CSO_LiveStrategy

Intraday Trading Strategy ( 15 min candlestick data )

Fresh_Entry and Position_Reversal : EMA 5 and DEMA 50 Crossover

SL_exit : Trailing stoploss in percent determined using clustering True Range values of the stock over a rolling period of last 200 days.  

Forced_exit : At market_close. Set at 15:15pm.

Strategy KPIs over last 200 days. Last refreshed on ( 30th Dec 2020 ) 

Backtested_on : ['RELIANCE']

============================ KPIs ==========================

CAGR:  198.0  %

Max_drawdown:  5.7  %

2.75 Settled Trades per ticker per day 

hit_ratio:  0.44

avg_profit:  24  points 

avg_loss:  11  points

risk:reward  0.46
