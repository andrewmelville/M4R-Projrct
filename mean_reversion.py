from rolling_functions import Rolling_LR
from plotting_functions import series_plot
import pandas as pd
import numpy as np



class TradingStrat():
    
    
    # This class holds different functions for trading strategies and the analysis
    # thereof. At the moment, we have a simple Mean-Reversion strategy which creates signals
    # determined by the residuals of an appropriate rolling linear regression
    
    
    def __init__(self):
        
        self.residuals_df = []
        self.lookback = []
        self.chunk_size = []
        self.signals_df = []
    
    
    def MeanReversion(self, currency_returns, commods_returns, chunk_size = 30, lookback = 10):
        
        # Initialise class variables
        self.lookback = lookback
        self.chunk_size = chunk_size

        
        # Create df of residuals using Residuals function
        self.residuals_df = self.Residuals(commods_returns, currency_returns)
        
        # Create df of chunk signals using Signals function
        self.signals_df = self.Signals()
        
        
        # Get daily (simple) commodities returns with same contracts as signal_df
        daily_returns = commods_returns.cumsum()

        # Multiply signals df by simple daily returns df to get daily P/L for each contract
        commod_PL = self.signal_df * daily_returns
        
        # Sum across columns for daily P/L, cumsum daily P/L for P/L curve
        PL_curve = commod_PL.sum(axis=1).cumsum()
        
        # Plot P/L Curve
        series_plot(pd.DataFrame(PL_curve),'P ')

        return self.signal_df
    
        
    def Residuals(self, commods_returns, currency_returns):
        
        ## This function creates a dataframe of commoditiy residuals from a 
        ## rolling linear regression onto a basket of currencies. These residuals
        ## will then be used to create several dataframes of trading signals.
        
        # Create empty residual dataframe
        self.residuals_df = pd.DataFrame().reindex_like(commods_returns)
        
        # Loop through each commodity
        for i, commod in enumerate(commods_returns):
            
           # Fit rolling regression of commodity onto currency average and take
           # prediction series
           roll_reg = Rolling_LR()
           roll_reg.fit(commods_returns, currency_returns, lookback = self.lookback)
           pred_series = roll_reg.pred_series()
           
           self.residuals_df[commod] = commods_returns[commod] - pred_series['Prediction']
           
           print('{} residuals completed {}/{}'.format(commod, i+1, commods_returns.shape[1]))
        
        return self.residuals_df
    
    def Signals(self):
        
        ## This function takes a df of residuals and splits it into chunks of a
        ## specified size. The residuals are then averaged over the chunk, ranked,
        ## and then a signal is applied to the contract for the month after, held
        ## in signals_df
        
        # Create empty signals df
        self.signal_df = pd.DataFrame([0]).reindex_like(self.residuals_df)
        
        # Split full returns data of commodities 
        # into chunks that are to be used as trading windows.
        chunk_list = np.array_split(self.residuals_df, np.floor(len(self.residuals_df) / self.chunk_size))
        
        # Loop through each trading chunk and make a df of that chunks residuals
        for i, chunk in enumerate(chunk_list[:-1]):
    
            # Average residuals over current chunk
            current_chunk_list = chunk.mean().sort_values(axis=0,ascending = False)
            
            # Get top three positive residual contracts
            pos_mask = current_chunk_list > 0
            sell_list = current_chunk_list[pos_mask]
            
            # Mask to select month ahead
            signal_mask = chunk_list[i+1].index

            # Assign negative value to contracts for month ahead
            self.signal_df.loc[signal_mask, sell_list.index[:3]] = 1
            
            
            # Get bottom three negative residual contracts
            neg_mask = current_chunk_list < 0
            buy_list = current_chunk_list[neg_mask]
            
            # Assign postive value to contracts for month ahead
            self.signal_df.loc[signal_mask, buy_list.index[-3:]] = -1
        
        return self.signal_df

#%%         Trading strategy: 
# # Long bottom three negative residuals, Short top three postive residuals.



    

# # Get daily (simple) commodities returns with same contracts as signal_df
# daily_returns = df_dict['Close'][signal_df.columns].loc[signal_df.index].fillna(method='ffill').diff()

# # Multiply signals df by simple daily returns df to get daily P/L for each contract
# contract_PL = signal_df * daily_returns

# # Sum across columns for daily P/L, cumsum daily P/L for P/L curve
# PL_curve = contract_PL.sum(axis=1).cumsum()

# # Plot P/L Curve
# series_plot(pd.DataFrame(PL_curve),'P ')
# # #%%     Trading Strategy:
# # # Long top three and Short bottom three residuals regardless of direction.



# # # Create empty signals df
# # signal_df = pd.DataFrame([0]).reindex_like(residual_df)
# # signal_df = signal_df.fillna(0)

# # # Loop through each month and make a df of that months residuals
# # for i in range(2012,2021):
# #     for j in range(1,13):
        
# #         mask = (residual_df.index > '{}-{}-01'.format(i,j)) & (residual_df.index <= '{}-{}-{}'.format(i,j,calendar.monthrange(i,j)[1]))
# #         month = residual_df.loc[mask]
# #         current_month_list = month.mean().sort_values(axis=0,ascending = False)
        
# #         # Go long bottom three contracts (signal shows over-performance)
# #         buy_list = current_month_list[-3:]
        
# #         # Mask to select month ahead
# #         signal_mask = (signal_df.index > pd.to_datetime('{}-{}-01'.format(i,j)) + relativedelta(months=1)) & (signal_df.index <= pd.to_datetime('{}-{}-{}'.format(i,j,calendar.monthrange(i,j)[1])) + relativedelta(months=1))
        
# #         # Assign positive value to contracts for month ahead
# #         signal_df.loc[signal_mask, buy_list.index] = 1
        
        
# #         # Go short top three contracts (signal shows under-performance)
# #         sell_list = current_month_list[:3]
        
# #         # Assign negative value to contracts for month ahead
# #         signal_df.loc[signal_mask, sell_list.index] = -1
    

# # # Get daily (simple) commodities returns with same contracts as signal_df
# # daily_returns = df_dict['Close'][signal_df.columns].loc[signal_df.index].fillna(method='ffill').diff()

# # # Multiply signals df by simple daily returns df to get daily P/L for each contract
# # contract_PL = signal_df * daily_returns

# # # Sum across columns for daily P/L, cumsum daily P/L for P/L curve
# # PL_curve = contract_PL.sum(axis=1).cumsum()

# # # Plot P/L Curve
# # series_plot(pd.DataFrame(PL_curve),'P/L Curve')