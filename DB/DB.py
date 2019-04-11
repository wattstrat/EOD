if __debug__:
    import logging
    logger = logging.getLogger(__loader__.name)

"""
    This class represent the METEOR databases interface.
    All databases classes inherit to this class.
"""


class DB(object):

    def __init__(self, *args, **kwargs):
        super().__init__()

    def get_error(self):
        raise NotImplementedError("This function is not implemented yet !")

    def insert(self, key=None, value=None, **kwargs):
        raise NotImplementedError("This function is not implemented yet !")

    def update(self, key=None, value=None, query=None, **kwargs):
        raise NotImplementedError("This function is not implemented yet !")

    def find(self, key=None, query=None, **kwargs):
        raise NotImplementedError("This function is not implemented yet !")

    def delete(self, key=None, query=None, **kwargs):
        raise NotImplementedError("This function is not implemented yet !")
