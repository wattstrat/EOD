import numpy as np


def sigmoid(time_weight, transition, speed):
    '''
    sigmoid function computed at time_weight, such that f(0)=0, f(1)=1, it transits at transition,
    with a given speed (the higher the faster the transition)
    '''
    non_rescaled0 = 1 / (1 + np.exp(speed * (transition)))
    non_rescaled1 = 1 / (1 + np.exp(-speed * (1 - transition)))
    non_rescaledt = 1 / (1 + np.exp(-speed * (time_weight - transition)))
    return (non_rescaledt - non_rescaled0) / (non_rescaled1 - non_rescaled0)
