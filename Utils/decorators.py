import numpy as np

import Config.config as config


def nonzero_pct_rep(func):
    def _decorator(self, *args, **kwargs):
        temp = func(self, *args, **kwargs)
        return temp + config.NONZERO_VAL
    return _decorator
