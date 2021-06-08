
"""
    This class inherits BasicStrategy constructor and functions
    It tries to predict large statistically meaninful spikes, that last multiple minutes, and happen around mean reversion cross over points.
    
    It first checks to see if a mean reversion happened within the past minute.
    It then checks to see if the price increase is believed to statistically significant (or is it just another small random blip).
    It then checks the slope of the short term moving average to try to ensure it is a large enough spike to last a few minutes time. 
    It then check the the difference between the short term and long term moving averges (to prevent flat slopes or oscillations) too closely together).
    
    If all of these conditions are met, it then checks account conditions (is there enough money to purchase, etc). 
    It then attemps to place a stop-loss order with a default high water mark. 
    A bracket order would be preferred, but Alpaca's API rejects orders with narrow take-profit and stop-loss conditions.
    
    Alpaca will let orders be identified with custom client id's, but once an order is executed and turned into a position, it isn't possible to identify it
    To avoid duplicates, all stategies will be prohibited from purchasing a stock that already has a order/position for it.

    Selling the position is done by checking the unrealized-profit of a position versus the variation in the stock price. 
    If the timing was correct, and the order was executed at the beginning of a large spike, then the take-profit should be related to the short term std dev.
"""
    


#basic libraries
import pandas as pd
import numpy as np
import time
import datetime
from pytz import timezone

#algo brokerage api
from alpaca_trade_api.rest import TimeFrame
import alpaca_trade_api as tradeapi

#stats package
from statsmodels.tsa.stattools import adfuller

#inherited class
from BasicStrategy import *


class StrategyBuyFiveMinuteSpikes(BasicStrategy):
    
    
    def __init__(self, new_name, new_trade_api_rest, new_stock_list,new_allocated_max,new_long, new_short,new_slope_duration, new_slope_threshold,new_short_long_slope_diff_threshold, new_target_profit):
   
        BasicStrategy.__init__(self,new_name,new_trade_api_rest,new_stock_list,new_allocated_max)
                      
        #variables to define how many minutes of delay to do the calculations on
        self.long_duration = new_long
        self.short_duration = new_short
        self.short_slope_duration = new_slope_duration
        self.short_slope_threshold = new_slope_threshold
        self.short_long_slope_diff_threshold = new_short_long_slope_diff_threshold
        self.target_profit_per_trade = new_target_profit

        #sometimes the mean crossing point can happen a minute or two off from when the spike becomes statistically significant
        #in the future modify this variable to be an array that keeps track of the last minute data for each stock to capture these near-misses
        self.previous_adf_bool = False
        self.previous_crossing_buy_bool = False

        self.current_adf_bool = False
        self.current_crossing_buy_bool = False

        
    def run_strategy(self):
        
    
        for i in range(len(self.stock_list)):

           
            stock = str(self.stock_list[i])
            print(f'inside for loop, strategy = {self.strat_name} and stock ticker = {stock}')
        
            #get a np array that contains all of this stock's closing data for the past duration, the +2 is because the long SMA will need more data to calculate
            this_stocks_close_np_array = self.get_historical_data_close_price_by_minutes(stock,self.long_duration+2)
          
            #if the data contains zeros or other errors, skip that stock and go to the next stock ticker
            if self.is_historical_data_clean(this_stocks_close_np_array):

                #keeping this line for future expansion, see comment above in constructor
                #self.previous_adf_bool = self.current_adf_bool
                #self.previous_crossing_buy_bool = self.current_crossing_buy_bool

                self.current_adf_bool = self.augmented_dickey_fuller_test_on_list(this_stocks_close_np_array)
                self.current_crossing_buy_bool = self.check_mean_reversion_of_long_and_short_sma_and_sma_slopes(this_stocks_close_np_array,self.long_duration,self.short_duration,self.short_slope_duration,self.short_slope_threshold,self.short_long_slope_diff_threshold)

                if (self.current_adf_bool or self.previous_adf_bool) and (self.current_crossing_buy_bool or self.previous_crossing_buy_bool):

                    #celebrate because an potential opportunity was found
                    self.found_opportunity()

                    #based on target profit per trade and how the stock's std dev, determine qty to buy
                    std_dev = this_stocks_close_np_array.std()
                    half_std_dev = std_dev / 2
                    qty_to_buy = round( self.target_profit_per_trade / half_std_dev) #round without a second parameter should return an int

                    #figure out costs and balances
                    current_price = this_stocks_close_np_array[-1] #-1 in the index gets the last element in the np array
                    current_cash = self.get_account_cash_as_float()
                    total_cost = current_price * float(qty_to_buy)
                    new_balance = current_cash - total_cost

                    #check to see if the strategy is allowed to spend that much of the balance
                    if new_balance > self.minimum_reserve_balance and total_cost < float(self.money_allocated_to_this_strategy):
                        #print(f'Found a trade and there is enough to cover this purchase, new balance = {new_balance} and the maximum allocation for this strategy is = ${self.money_allocated_to_this_strategy}')
                
                        if(self.check_if_stock_already_has_open_order_or_position(stock)):
                            print("Future version of this code might lift this limitation, once there is a way to corrolate client id's and positions.")
                            print("Not allowed to make this purchase since there are already open orders or positions for this stock.")
                        else:
                            print("Allowed to purchase this stock since there are no conflicting open orders or positions")
                            self.buy_market_ioc_and_add_trailing_stop_loss_percent(stock,qty_to_buy,1.0)

                    else: #balances
                        print('Found a trade, but there is not enough in the account to cover it.')

                else: #did not find buying opportunity
                    print('Inside else statement, did not find buying opportunity')
            else: #data is not clean
                print('Data is not usable, check to see if there are zeros or other anomolies in the data')
        
      
             

    def sell_positions_over_threshold(self):
        
        positions = self.alpaca.list_positions()

        for position in positions:
            
            #makes sure a strategy doesn't sell another strategies position
            if position.symbol in self.stock_list:

                print(f'There is an open position for symbol {position.symbol} that has an unrealized profit of {position.unrealized_pl}')
                
                if( float(position.unrealized_pl) > self.target_profit_per_trade ):
                
                    print("Made a profit! Closing any open orders for this symbol and then closing the position.")
              
                    # Clear any existing orders with the same stock symbol
                    orders = self.alpaca.list_orders(status="open")
                    for order in orders:
                        if order.symbol == position.symbol:
                            self.alpaca.cancel_order(order.id)

                    #closing the position
                    self.alpaca.close_position(position.symbol)
                
        

