"""
    This class is the parent class for all strategies and contains 
    all basic functions that ensure that the StrategyCollector operates as expected and
    all common math, stats, or account functions.
   
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


class BasicStrategy():
    
    def __init__(self,new_name, new_trade_api_rest, new_stock_list,new_allocated_max):
        self.strat_name = new_name
        self.alpaca = new_trade_api_rest
        self.account = self.alpaca.get_account()
        self.stock_list = new_stock_list
        self.money_allocated_to_this_strategy = new_allocated_max
        self.minimum_reserve_balance = 500
        self.opportunities_found_this_run = 0
        self.orders_made_this_run = 0
        
        #journal number for client id
        self.journal_id_int = 1
        #self.journal_reason = "" 


    #override this
    def run_strategy(self):
        print("This method is meant to be overridden in the child class. If this is printing, then that needs to be fixed.")


    #override this
    def sell_positions_over_threshold(self):
        print("This method is meant to be overridden in the child class. If this is printing, then that needs to be fixed.")


    def buy_market_ioc_and_add_trailing_stop_loss_price(self, stock, qty_to_buy,new_trail_price):
        
        #first send the market order, immediate or cancel
        self.alpaca.submit_order(
                symbol=stock,
                qty=qty_to_buy,
                side='buy',
                type='market',
                time_in_force='ioc'
                )

        #then send the trailing stop loss order, good till close      
        self.alpaca.submit_order(
            symbol=stock,
            qty=qty_to_buy,
            side='sell',
            type='trailing_stop',
            trail_price = new_trail_price,
            #trail_percent=trailing_stop_perc,  # if user enters 1.0, then stop price will be hwm*0.99
            time_in_force='gtc' #change this later?
            )

        
    def buy_market_ioc_and_add_trailing_stop_loss_percent(self, stock, qty_to_buy,new_trail_percent):
        
        #first send the market order, immediate or cancel
        self.alpaca.submit_order(
                symbol=stock,
                qty=qty_to_buy,
                side='buy',
                type='market',
                time_in_force='ioc'
                )

        #then send the trailing stop loss order, good till close      
        self.alpaca.submit_order(
            symbol=stock,
            qty=qty_to_buy,
            side='sell',
            type='trailing_stop',
            trail_percent=new_trail_percent,  # if user enters 1.0, then stop price will be hwm*0.99
            time_in_force='gtc' #change this later?
            )


    def check_if_stock_already_has_open_order_or_position(self, stock):
    
        positions = self.alpaca.list_positions()
        
        for position in positions:
            if stock == position.symbol:
                return True
    
        orders = self.alpaca.list_orders(status="open")
        
        for order in orders:
            if stock == order.symbol:
                return True
        
        return False
        

    def print_all_positions(self):
        positions = self.alpaca.list_positions()
        for position in positions:
          print(position)


    def print_opportunities_found_this_run(self):
        print(f"The strategy {self.strat_name} has found {self.opportunities_found_this_run} this many opportunities this run")
        

    def found_opportunity(self):
        print('***************************************')
        print('***********winner winner***************')
        print('**********chicken dinner***************')
        print('***************************************')
        self.opportunities_found_this_run += 1   
        

    def get_account_cash_as_float(self):
        #alpaca returns all numbers as strings to not lose any precision, will have to cast to float
        cash = float(self.account.cash)
        print(f"This account has this much cash available: ${cash}")
        return cash


    def clear_all_open_orders():
        # Clear existing orders again.
        orders = self.alpaca.list_orders(status="open")
        for order in orders:
          self.alpaca.cancel_order(order.id)

    #based on the /v1 version of the API
    def get_historical_data_close_price_by_minutes(self, stock,number_of_data_points):
        barset = self.alpaca.get_barset(stock,'minute',limit = number_of_data_points)
        close_price_np_array = barset.df[(stock,'close')].values 
        return close_price_np_array


    #based on the /v1 version of the API
    def get_historical_data_close_price_by_fifteen_minutes(self, stock,number_of_data_points):
        barset = self.alpaca.get_barset(stock,'15Min',limit = number_of_data_points)
        close_price_np_array = barset.df[(stock,'close')].values 
        return close_price_np_array

    #based on /v1 of API
    def get_historical_data_volume_by_minutes(self, stock,number_of_data_points):
        barset = self.alpaca.get_barset(stock,'minute',limit = number_of_data_points)
        #close_price_np_array = barset.df[(stock,'close')].values 
        volume_np_array = barset.df[(stock,'volume')].values
        #add error handling here for if barset goes wrong
        return volume_np_array


    def is_historical_data_clean(self, close_price_np_arry):
        return_bool = False
        zero_value = 0.00

        if zero_value in close_price_np_arry:
            print("Data is not clean - contains one or more zeros! Do not use this data.")
            pass #keep return_bool equal to false
        else:
            print("Data is clean! :)")
            return_bool = True

        return return_bool


    def augmented_dickey_fuller_test_on_list(self, close_price_np_array):
    
        result = adfuller(close_price_np_array)
   
        #print(f'ADF Statistic: {result[0]}')
        #print(f'n_lags: {result[1]}')
        #print(f'p-value: {result[1]}')

        if result[1] > .05:
          print(f'p value is good, {result[1]}')
          is_p_good = True
        else:
          print(f'p value is bad', {result[1]})
          is_p_good = False

        adf_metric = 0
        #for temp, temp_adf_metric in result[0]:
        #  adf_metric = temp_adf_metric
        adf_metric = result[0]

        print(f'ADF Metric = {adf_metric}')
        are_criticals_good = True
        temp_bool = True
        for key, value in result[4].items():
            #print(f'Critical Values:   {key}, {value}') 
            if adf_metric > value:
              temp_bool = True
              print(f'adf_metric = {adf_metric} is GREATER than value = {value}')
            else:
              temp_bool = False
              print(f'adf_metric = {adf_metric} is LESS than value = {value}')

            are_criticals_good = are_criticals_good and temp_bool

        is_stationary = is_p_good and are_criticals_good
        if is_stationary:
         
          print(f'This ADF shows the time series is stationary because {is_p_good} and {are_criticals_good}')
        else:
          self.journal_reason = "ADF Test shows time series is NOT stationary because ADF Metric = " + str(adf_metric)
          print(f'This ADF shows the time series is NOT stationary because {is_p_good} and {are_criticals_good}.')

        return is_stationary
    

    def check_mean_reversion_of_long_and_short_sma(self, close_price_list,long,short):

        data = pd.DataFrame(close_price_list)

        sma_long = data[0].rolling(window=long).mean()
        sma_short = data[0].rolling(window=short).mean()
      
        #adds columns for simple moving average
        data['SMA_LONG']=sma_long
        data['SMA_SHORT']=sma_short
    
        #test to see if it crosses over, add to the dataframe
        previous_SHORT = data['SMA_SHORT'].shift(1)
        previous_LONG = data['SMA_LONG'].shift(1)
        crossing_buy = ((data['SMA_SHORT'] > data['SMA_LONG']) & (previous_SHORT <= previous_LONG))
        data['Crossing_Buy'] = crossing_buy
        data['previous_SHORT'] = previous_SHORT
        data['previous_LONG'] = previous_LONG
    
        #prints for testing purposes
        #print(data.tail(5))

        if data['Crossing_Buy'].tail(1).values[0]:
          print("Crossing Buy Signal Found")
          print(data.tail(1))
          return True
        else:
          print("Crossing Buy Signal *NOT* Found")
          return False


    def check_mean_reversion_of_long_and_short_sma_and_sma_slopes(self, close_price_list,long,short,new_t,new_slope_min,new_slope_diff_min):
        
        data = pd.DataFrame(close_price_list)

        sma_long = data[0].rolling(window=long).mean()
        sma_short = data[0].rolling(window=short).mean()
        
        #adds columns for simple moving average
        data['SMA_LONG']=sma_long
        data['SMA_SHORT']=sma_short

        #print(data.head())
    
        delta_t = new_t


        #test to see if it crosses over, add to the dataframe
        previous_SHORT = data['SMA_SHORT'].shift(1)
        previous_LONG = data['SMA_LONG'].shift(1)
        crossing_buy = ((data['SMA_SHORT'] > data['SMA_LONG']) & (previous_SHORT <= previous_LONG))
        data['Crossing_Buy'] = crossing_buy
        data['previous_SHORT'] = previous_SHORT
        data['previous_LONG'] = previous_LONG
        data['diff_SHORT'] = data['SMA_SHORT'].diff(delta_t)/delta_t
        data['diff_LONG'] = data['SMA_LONG'].diff(delta_t)/delta_t
        data['diff_delta'] = data['diff_SHORT'] - data['diff_LONG']
        
        #print(data.tail(5))

        if data['Crossing_Buy'].tail(1).values[0] and data['diff_SHORT'].tail(1).values[0] > new_slope_min and data['diff_delta'].tail(1).values[0] > new_slope_diff_min:
          print("Crossing Buy Signal Found")
          print(data.tail(1))
          return True
        else:
          print("Crossing Buy Signal *NOT* Found")
          return False

          
    def reset_journal_reason(self):
        print("future expansion")
        #self.journal_reason = ""

        
    def get_buying_power(self):
        # Check how much money we can use to open new positions.
        print('${} is available as buying power.'.format(self.account.buying_power))
        return self.account.buying_power


    def print_all_open_orders(self):
        print('Printing all open orders.')
        orders = self.alpaca.list_orders(status="open")
        if len(orders) > 0:
          for order in orders:
            print(order)
        else:
          print('There are no open orders at this time.')


    def buy_market_order_with_brackets(self, qty, stock, stop_loss_stop_price, stop_loss_limit_price, take_profit_price, client_id,current_price):
        print(f'Trying to place a bracket order for {qty} shares of {stock} that is currently at {current_price}')
        print(f'The stop loss is set to {stop_loss_stop_price} and the limit is {stop_loss_limit_price}, the take profit is {take_profit_price}')

        self.alpaca.submit_order(
           symbol=stock,
           qty=qty, 
           side='buy',
           type='market',
           time_in_force='gtc', 
           order_class='bracket',
           client_order_id = client_id,
           stop_loss={'stop_price': stop_loss_stop_price,
                     'limit_price':  stop_loss_limit_price},
           take_profit={'limit_price': take_profit_price}
           )
  
