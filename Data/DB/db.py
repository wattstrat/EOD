

from Data.data import Data

if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class DB(Data):

    """
            Data objects, i.e how to access data when trying to compute results.
            Can take multiple form, mainly cache, DB, or to be built child classes
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    """
        Commented because parent implement logic in these functions
        """
    # def get_val(self, varName, *args, **kwargs):
    # raise NotImplementedError("Data.DB.db.DB.get_val error: The get function
    # is not implemented yet !")

    # def set_val(self, varName, value, *args, **kwargs):
    #         raise NotImplementedError("Data.DB.db.DB.set_val error: The get function is not implemented yet !")
    # def clear(self):
    # raise NotImplementedError("Data.DB.db.DB.set_val error: The get function
    # is not implemented yet !")
