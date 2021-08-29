# -*- coding: utf-8 -*-
"""
Created on Thu Jun  3 10:19:11 2021

@author: andre
"""

from rolling_functions import Rolling_LR, Rolling_LR_OneD, LSTM_predictor
from plotting_functions import series_plot
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import spearmanr

class MeanReversion():
    
    
    # This class holds different functions for trading strategies and the analysis
    # thereof. At the moment, we have a simple Mean-Reversion strategy which creates signals
    # determined by the residuals of an appropriate rolling linear regression
    
    
    def __init__(self):
        
        self.residuals_df = []
        self.lookback = []
        self.chunk_size = []
        self.signals_df = []
    
    
    def back_test(self, currency_returns, noisy_commods_returns, commod_prices, chunk_size, lookback, verbose=False, pos_ratio=1/3):  
        
        self.chunk_size = chunk_size        # Size of each trading period
        self.lookback = lookback            # Number of days considered in each regression
        self.verbose = verbose              # Print fitting checkpoints
        self.pos_ratio = pos_ratio          # What proportion of the full basket of commoditis to long and short in
        self.commod_number = noisy_commods_returns.shape[1]

        self.noisy_commods_returns = noisy_commods_returns # These are the returns that all strategies/models will trade on
        self.currency_returns = currency_returns # Currency returns for model fitting
        self.commod_prices = commod_prices
        self.daily_prices = commod_prices
        
        # Create empty residual dataframe
        self.residuals_df = pd.DataFrame([0]).reindex_like(self.noisy_commods_returns)
        self.beta_df = pd.DataFrame([]).reindex_like(self.noisy_commods_returns)
        self.LR_pred_series = pd.DataFrame([]).reindex_like(self.noisy_commods_returns)
        self.LSTM_pred_series = pd.DataFrame([]).reindex_like(self.noisy_commods_returns)
        
        # Perform trade passes at each level of noise in noise_props for comparison of performance

        self.LR_performance = self.trade(noisy_commods_returns, "LR", pos_ratio)
        # self.LSTM_performance = self.trade(noisy_commods_returns, "LSTM", pos_ratio)

    
    def trade(self, added_noise_commods_returns, model, pos_rat):
        
        ## This function creates a signal from the class variable dataframe of residuals
        ## which are clauclated before this function is called. It then performs
        ## the trading over the testing period by multiplying this signal df
        ## against the prices for each day to generate a PL curve.
        
        # Create dfs of chunk signals using signals function for chosen model
        if model == "LR":
            self.LR_Residuals(added_noise_commods_returns)
        
        elif model == "LSTM":
            self.LSTM_Residuals(added_noise_commods_returns)
        
        
        # Create df of chunk signals using Signals function
        self.pos_ratio = pos_rat
        self.Signals()
        
                                                
        # Multiply signals df by simple daily prices df to get daily P/L for each contract
        commod_PL = self.signal_df * self.daily_prices
        
        # Sum across columns for daily P/L, cumsum daily P/L for P/L curve
        PL_curve = commod_PL.sum(axis=1).cumsum()

        return PL_curve
    
        
    def LR_Residuals(self, commods_returns):
        
        ## This function creates a dataframe of commodity residuals from a 
        ## rolling linear regression onto a currency averages returns. These residuals
        ## will then be used to create dataframes of trading signals for each trading period.
        
        # Loop through each commodity
        for i, commod in enumerate(commods_returns.columns):

            # Regress currency average onto commodities returns and take # prediction series            
            roll_reg = Rolling_LR_OneD()
            roll_reg.fit(commods_returns[commod].iloc[int(0.5*commods_returns.shape[0]):], self.currency_returns.iloc[int(0.5*commods_returns.shape[0]):], lookback=self.lookback)

            self.LR_pred_series[commod] = roll_reg.pred_ts
            self.beta_df[commod] = roll_reg.beta_df
            # self.residuals_df[commod] = self.noisy_commods_returns[commod] - self.LR_pred_series[commod]
            
            self.residuals_df[commod] = np.random.normal(0,1,self.LR_pred_series.shape[0])
            
            # print('{} residuals completed {}/{}'.format(commod, i+1, commods_returns.shape[1]))
            
    def LSTM_Residuals(self, commods_returns):
        
        ## This function creates a dataframe of commodity residuals from a 
        ## LSTM model. These residuals will then be used to create dataframes 
        ## of trading signals for each trading period.
        
        # Loop through each commodity
        for i, commod in enumerate(commods_returns.columns):
            
            # Regress currency average onto commodities returns and take
            # prediction series    
            lstm_class = LSTM_predictor()
            
            lstm_class.train(pd.DataFrame(commods_returns[commod]), self.currency_returns, lookback=self.lookback)
            self.LSTM_pred_series[commod].iloc[int(0.5*commods_returns.shape[0]) + self.lookback + 1:] = lstm_class.test()
            
            self.residuals_df[commod] = self.noisy_commods_returns[commod] - self.LSTM_pred_series[commod]
            # self.residuals_df[commod] = np.random.normal(0,1,self.noisy_commods_returns.shape[0])
            print('{} LSTM residuals completed {}/{}'.format(commod, i+1, commods_returns.shape[1]))
    
    
    def Signals(self):
        
        ## This function takes a df of residuals and splits it into chunks of a
        ## specified size. The residuals are then averaged over the chunk, ranked,
        ## and then a signal is applied to the contract for the month after, held
        ## in signals_df
        
        # Create empty signals df
        self.signal_df = pd.DataFrame([0]).reindex_like(self.residuals_df)
        self.pred_chunk_rank_list = []
        
        # Split full returns data of commodities into chunks that are to be used as trading windows.
        chunk_list = np.array_split(self.residuals_df, np.floor(len(self.residuals_df) / self.chunk_size))
        
        # Determine how many positions to take long and short
        pos_num = int(self.pos_ratio * self.noisy_commods_returns.shape[1])

        # Loop through each trading chunk and make a df of that chunks signals
        for i, chunk in enumerate(chunk_list[:-1]):
    
            # Average residuals over current chunk
            current_chunk_list = chunk.mean().sort_values(axis=0, ascending=False)
            self.pred_chunk_rank_list.append(current_chunk_list.index)
            
            # Get top three positive residual contracts
            pos_mask = current_chunk_list > 0
            sell_list = current_chunk_list[pos_mask]
            
            # Mask to select month ahead
            signal_mask = chunk_list[i+1].index
            
            # Assign negative (sell) value to contracts for month ahead
            self.signal_df.loc[signal_mask[0], sell_list.index[:pos_num]] = 1/(2*pos_num)
            self.signal_df.loc[signal_mask[-1], sell_list.index[:pos_num]] = -1/(2*pos_num)
            
            # Get bottom three negative residual contracts
            neg_mask = current_chunk_list < 0
            buy_list = current_chunk_list[neg_mask]
            
            # Assign positive (buy) value to contracts for month ahead
            self.signal_df.loc[signal_mask[0], buy_list.index[-pos_num:]] = -1/(2*pos_num)
            self.signal_df.loc[signal_mask[-1], buy_list.index[-pos_num:]] = 1/(2*pos_num)
        
    def beta_plot(self):
     
        ## Plot time series of estimated beta coefficients
        
        # Plot beta time series
        plt.figure(figsize=(20,10))
        for col in self.beta_df.columns:    
           plt.plot(self.beta_df[col], lw=1, label=col)
       
        plt.xlabel('Index')
        plt.ylabel('Value')
        plt.title('Estimated Beta Coefficients that generated residual signals')
        plt.legend(loc=3)
        plt.show()