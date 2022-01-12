# -*- coding: utf-8 -*-
"""
@author: Ambiwlans
@general: EnTest - English Vocab testing site
@description: Utils
"""

#Math
import numpy as np
from scipy.stats import norm

##########################################
### HELPER FNs
##########################################

# Our sigmoid/logistic function that we fit to the data
# e term allows a warp to find upper/lower bounds
def sigmoid(x, t, a, e):
    return (1 / (1 + np.exp(t*(x-a)))) ** e

# Inverse of the logistical/sigmoid fn
    # used to grab x vals given y on our sigmoid
def logit(y, t, a):
    if y == 0:
        y = 0.00001
    if t == 0:
        t = 0.00001
    x = (np.log((1/y) - 1))/t + a
    return x

# Custom cost fn
    # used to fit our curve
    # Expected Ranges: 
        # Unregularized cost is 0~1
        # cost of 1 means that the prediction is 100% wrong
        
        # reg should be 0~.1
        
        # 0<t<inf
        # t is very steep > .1
        # t is shallow < .0001
        
        # 0<a<10000
        # ~5000 is average but this value need not be particularly penalized
def sigmoid_cost_regularized(params, true_X, true_Y, last_t, last_a, default_t):
    reg = 0
    t, a = params    
    i = len(true_X)
    
    if i == 0: print("Shouldn't happen 15398")
    
    # Get predictions from our sigmoid    
    pred_Y = sigmoid(true_X, t, a, 1)
    
    # Calculate the sample bias correcting array
        # Cortes, C., Mohri, M., Riley, M., & Rostamizadeh, A. (2008, October). Sample selection bias correction theory. In International conference on algorithmic learning theory (pp. 38-53). Springer, Berlin, Heidelberg.
            # https://cs.nyu.edu/~mohri/pub/bias.pdf
    
    #Fit a line across whole dataset
        # using a gaussian distribution for a close enough estimate (reality will be slightly left biased and have a clipped top)
        # Invert the dist for cost weights to correct sample bias    
    
    mean,std=norm.fit(true_X)
    dist = norm(mean,std)
    weights = dist.pdf(true_X)
    
    if i == 1:
        weights = 1
        
    #Regularization penalties
    
    #Clip OOB values
    if t <= 0.0001: return 1000 * abs(t - 0.0001) + 100
    if a < 1: return abs(a - 1) + 100
    
        
    #Penalize very large jumps
    reg += np.log((t / last_t) + (last_t / t) - 1) / i  
    reg += (max(abs(a - last_a) - 100, 0) / last_a) / 5

    #Penalize low y values at x=1
    low_y_affect_size = .0000001                                             # reg term multiplier
    ugliness = max(((1 - sigmoid(1, t, a, 1)) * 50)**5, 1)-1               # y=1->0 y=.9->.00015 y=.75->.015 y=.5->0.5
    reg += low_y_affect_size * ugliness
    
    #Penalize shallowness while a is small and early in test
    early_shallow_affect_size = .1                                                    # reg term multiplier
    shallowness = np.log((default_t / t) + np.e)                         # (even = .3, steep = .07, shallow = 2~3)
    bigness = 500000/(a**2 + 500000)                                    # ignore bigger a (1->1, 500 -> .6, 5000 -> .2)
    earliness = 100 / (i**2.5 + 100)                                      # fall off term (1 -> 1, 15 -> .2, 50->.018, 100->.004)
    
    reg += early_shallow_affect_size * shallowness * bigness * earliness
    
    #Penalize steepness while early in test
    early_steep_affect_size = .05                                                    # reg term multiplier
    steepness = np.log((t / default_t) + np.e)                           # (even = .3, steep = 2~3, shallow = .07)
    earliness = 100 / (i**3 + 100)                                      # fall off term (1 -> 1, 15 -> .2, 50->.018, 100->.004)
    
    reg += early_steep_affect_size * steepness * earliness

#    print('Penalize very large jumps')
#    print(f"t- {last_t} -> {t} ... jump pen- {np.log((t / last_t) + (last_t / t) - 1)}")
#    print(f"a- {last_a} -> {a} ... jump pen- {(max(abs(a - last_a) - 100, 0) / last_a) / 5}")
#    
#    print('Penalize low y values at x=1')
#    print(f"ug- {low_y_affect_size * ugliness}")
#    
#    print("Penalize shallowness while a is small and early in test")
#    print(f"as- {early_shallow_affect_size} sh- {shallowness} big- {bigness} earl- {earliness}")
#    print(f"tot- {early_shallow_affect_size * shallowness * bigness * earliness}")
#    
#    print("Penalize steepness while early in test")
#    print(f"as- {early_steep_affect_size} st- {steepness} earl- {earliness}")
#    print(f"tot- {early_steep_affect_size * steepness * earliness}")
#    
#    print("Totals")
#    print(f"Maincost- {np.mean(((pred_Y - true_Y)**2)/weights)*(np.mean(weights))} Totalreg- {reg}")
#    print("")
    
    return np.mean(((pred_Y - true_Y)**2)/weights)*(np.mean(weights)) + reg