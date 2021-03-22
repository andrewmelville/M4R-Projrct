# -*- coding: utf-8 -*-
"""
Created on Mon Mar 22 20:48:44 2021

@author: andre
"""

import numpy as np
import pandas as pd

from plotting_functions import series_plot

class ARMAmodel():
        
    def __init__(self):
        
        pass
    
    def __call__(self, n=10000, phi=[], theta=[], sigma=[], burnin=0):
        
                ## Function inputs:
            
        # n: length of generated series    
        # phi: array of p AR coefficients
        # theta: array of q MA coefficients
        # sigma: standard deviation of Gaussian noise
        # burnin: number of observations to be discarded
    
        self.n = n
        self.phi = phi
        self.theta = theta
        self.sigma = sigma
        self.burnin = min(burnin, len(phi))
        self.p = len(phi)
        self.q = len(theta)
        
        return self.ARMA()
        
    
    def ARMA(self):
        
        # Set initial conditions
        e = np.random.normal(loc=0, scale=self.sigma, size=2*self.n)
        x = np.array([0.0] * (self.n + self.burnin))
        x[0:self.p] = 0
        
        # Loop to generate full series
        for t in range(max(self.p, self.q), self.n + self.burnin):
            
            x[t] = np.dot(x[t-self.p:t], self.phi) + np.dot(e[t-self.q:t], self.theta) + e[t+1]
            
        return pd.DataFrame(x[self.burnin:])
    
arma = ARMAmodel()
l=5
x=arma(n=20000,
     phi=[1/l for i in range(l)],
     theta=[0]*40 +[-1]*20,
     sigma=0.001,
     burnin=1000)

series_plot(x,'')