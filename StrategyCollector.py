"""
    This class is organizes and operates all strategies.
    In future improvements, this would be the place to implement multi-threading to improve performance. 
   
"""

import pandas as pd
import numpy as np
import time
import datetime
from pytz import timezone

from alpaca_trade_api.rest import TimeFrame

import alpaca_trade_api as tradeapi
from statsmodels.tsa.stattools import adfuller



class StrategyCollector():
  

    def __init__(self, trade_api_rest):
        
        self.strat_list = []
        self.alpaca = trade_api_rest
        self.account = self.alpaca.get_account()
        self.disable_shorting()
        self.print_my_account_configurations()


    def append_strat(self, new_strat):
        self.strat_list.append(new_strat)
        print("Inside Strat Collector, appended new strategy.\n")


    def run_strat_collector(self):
                        
      #begin looping until the market closes
      while self.alpaca.get_clock().is_open:
                
        self.start_time_of_loop = self.alpaca.get_clock().timestamp.replace(tzinfo=datetime.timezone.utc).timestamp()
      
        print("\n\nRunning Strategies:")
        for strat in self.strat_list:
            strat.run_strategy()

        print("\n\nPositions:")
        for strat in self.strat_list:
            strat.sell_positions_over_threshold()
        
        print("\n\nOpportunities Found Today:")
        for strat in self.strat_list:
            strat.print_opportunities_found_this_run()


        self.end_time_of_loop = self.alpaca.get_clock().timestamp.replace(tzinfo=datetime.timezone.utc).timestamp()
       
        #slows down loop to once a minute
        while_loop_difference = int((self.end_time_of_loop - self.start_time_of_loop))
        print(f"\nWaiting inside the function run_start_collector: time = {self.end_time_of_loop} and time difference = {while_loop_difference} in seconds")

        if while_loop_difference < 60:
            time.sleep(59-while_loop_difference)
                
        print("\n\n\n")



    def check_if_account_is_blocked(self):
        # Check if our account is restricted from trading.
        if self.account.trading_blocked:
            print('Account is currently restricted from trading.')
            return True
        else:
            print('Account is not blocked.')
            return False

    def print_my_account_configurations(self):
        print(self.alpaca.get_account_configurations())

    def disable_shorting(self):
        self.alpaca.update_account_configurations(True,None,None,None)
        print('Short selling is now disabled on this account.')
        return False




    
    def get_list_of_all_tradable_stock_tickers(self):
        
        tradable_stocks = []

        active_assets = self.alpaca.list_assets(status='active')
        for asset in active_assets:
            if asset.tradable:
                tradeable_stocks.append[asset.symbol]            
                #print('The stock {} is being sold on the {} exchange'.format(asset.symbol,asset.exchange))
            #ends if
        #ends for
        return tradable_stocks



    # Wait for market to open.
    def awaitMarketOpen(self):
        isOpen = self.alpaca.get_clock().is_open
    
        if isOpen:
            print('Market is already open.')
        else:
            print('Market is not yet open, waiting for it to open.')
            while(not isOpen):
                clock = self.alpaca.get_clock()
                openingTime = clock.next_open.replace(tzinfo=datetime.timezone.utc).timestamp()
                currTime = clock.timestamp.replace(tzinfo=datetime.timezone.utc).timestamp()
                timeToOpen = int((openingTime - currTime) / 60)
                print(str(timeToOpen) + " minutes til market open.")
                time.sleep(60)        
                isOpen = self.alpaca.get_clock().is_open



