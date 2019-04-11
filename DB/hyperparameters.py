

from Inputs.DB.Hyperparameters.idmw import HyperIdmw

if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class HyperparamComputation(object):

    def __init__(self, *args, **kwargs):
        self.run(*args, **kwargs)

    def compute_hyp_idmw(self):
        if __debug__:
            logger.info('Computing the hyperparameters for the interpolation method idmw')
        hyper_instance = HyperIdmw()
        my_param = hyper_instance()
        if __debug__:
            logger.info('The hyperparamters have been computed: %s', my_param)

    def run(self, parsed):
        if parsed['interpolate_idmw'] is True:
            self.compute_hyp_idmw()
