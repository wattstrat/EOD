"""
    Higher parent of Server classes.
    It raise and log some exceptions !
"""


class Server(object):

    """
    Initialization class.
    """

    def __init__(self, instance_name=None, id_thread=None, **kwargs):
        super().__init__()
        self._instance_name = instance_name
        self._id_thread = id_thread

    def launch(self):
        raise NotImplementedError()
