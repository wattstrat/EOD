
import random
import time

from Server.server import Server
if __debug__:
    import logging
    logger = logging.getLogger(__name__)


# A Meteor Server who does nothing : just print some stuff
class MeteorServerTest(Server):
    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)

        self._id = random.randint(1, 100000)
        if __debug__:
            logger.debug("MeteorServer Test number %x", self._id)
        self._stop = False

    def launch(self):
        """
        Launch infinite loop and print stuff
        """
        if __debug__:
            logger.debug("Launch the Meteor Server Test (%x) on %s in %d thread",
                         self._id, self._instance_name, self._id_thread)
        while not self._stop:
            if __debug__:
                logger.info("%x is still here!", self._id)
            time.sleep(1)
        if __debug__:
            logger.debug("%x is asked to stop: stopping!", self._id)

    def stop(self):
        self._stop = True
