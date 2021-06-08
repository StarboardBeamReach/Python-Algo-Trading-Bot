"""
   This class connects with Alpaca Brokerage
   creates all investment strategies and stock lists
   provides that information to the StrategyCollector
   and runs the StrategyCollector
   
   It requires an account at Alpaca Brokerage
   which can be created at https://alpaca.markets/
   and API keys which a paper trading account.
   
"""
   

import pandas as pd
import alpaca_trade_api as tradeapi

from StrategyCollector import StrategyCollector
from StrategyBuyFiveMinuteSpikes import StrategyBuyFiveMinuteSpikes
from BasicStrategy import BasicStrategy


#overrides the print settings
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

#replace these with your accounts values
API_KEY = 12345678901234567890 
API_SECRET = 98765432109876543210
APCA_API_BASE_URL = "https://paper-api.alpaca.markets"

alpaca = tradeapi.REST(API_KEY, API_SECRET, APCA_API_BASE_URL, 'v2')


my_strat_collector = StrategyCollector(alpaca)


#highest tier, long
stocks_strat1 = ["AAPL", "AMZN","DIS","ISRG","GILD","NVS","JNJ","SHOP","GOOG","NFLX"]
strat1 = StrategyBuyFiveMinuteSpikes("Strat 1 - High Tier, Long",alpaca,stocks_strat1,5000,25,5,2,1.0,2.0,5.0)
my_strat_collector.append_strat(strat1)

#medium tier
stocks_strat4 = ["BAC", "F","XOM","T"]
strat4 = StrategyBuyFiveMinuteSpikes("Strat 2 - Medium Tier",alpaca,stocks_strat2,3000,20,4,2,1.0,2.0,5.0)
my_strat_collector.append_strat(strat4)

#low tier
stocks_strat5 = ["DOOO", "QRTEB", "BBAR", "NTB","SPLP","CODI","IIIN","CAI","SCSC","VEC","LOMA","AZZ","LEE","PFBC","RM","RBKB","GAIN","CRAI","BANF","PZN","ITRN","UNTY","SPNS","TSBK","SQBG","CNOB","MGIC","EFSC","SRT","CTT","PLUS","SGRP","CECE","FRME","CCB","CPF","FBNC","UEIC","KELYB","GFN","CALB","MCB","INOD","RUSHB","FBK","ECOL","SBFG","ESXB","MPX","FWRD","MHO","EVBN","TOWN","APOG","SRCE","HLIO","HMTV","MBWM","PAM","QCRH","APWC","NVEC","CSTR","SASR","AMNB","STXB","LEGH","BANR","BUSE","UVSP","DSGX","OPY","NVMI","FN","VCTR","SFST","MSBI","SONA","FBIZ","HMST","CBTX","LMRK","UONE","RBNC","FONR","MLR","FBMS"]
strat5 = StrategyBuyFiveMinuteSpikes("Strat 3 - Low Tier",alpaca,stocks_strat3,1000,20,4,2,1.0,2.0,5.0)
my_strat_collector.append_strat(strat5)



my_strat_collector.awaitMarketOpen()
my_strat_collector.run_strat_collector()
