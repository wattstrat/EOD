
import threading
import traceback
import Config.config as config
import Config.variables as variables

if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class PoolMeteorServer(object):

    def __init__(self, instance_name, args):

        self._threads = []
        self._args = args
        self._instance_name = instance_name

    def worker(self, instance_name, id_thread, meteor_name, cache, cache_opt, extra_queue=[]):
        if __debug__:
            logger.info("Init Worker : %s", meteor_name)
        local = threading.local()

        local.w = variables.loader.get_instance(meteor_name, instance_name=instance_name,
                                                id_thread=id_thread, cache=None,
                                                conf_queue={'queue_name': extra_queue})
        threading.current_thread().w = local.w

        cache_opt['meteor'] = local.w
        if isinstance(cache, str):
            local.cache = variables.loader.get_instance(cache, **cache_opt)
        else:
            local.cache = cache

        threading.current_thread().cache = local.cache
        local.w._cache = local.cache

        if __debug__:
            logger.info("Launching MeteorServer")
        try:
            local.w.launch()
        except Exception as e:
            if __debug__:
                logger.critical("Wild exception occured : %s\n======= backtrace ======\n%s", e, traceback.format_exc())
            else:
                raise
            local.w._current_job = {'type': ['DEAD'], 'id': 'Wild exception occured'}

    def launch(self):
        cache = self._args.cache_politic
        cache_opt = self._args.cache_politic_opt
        workers = self._args.workers
        meteor_workers = self._args.workers_name

        if __debug__:
            logger.info("Launching Server with %d workers (workers_name=%s, cache=%s)" %
                        (workers, meteor_workers, cache))
        # Create thread
        for i in range(workers):
            if len(meteor_workers):
                worker_name = meteor_workers.pop()
            else:
                worker_name = config.__DEFAULT_WORKER_NAME__
            extra_queue = []
            try:
                extra_queue = self._args.extra_queues[i]
            except IndexError:
                pass
            t = threading.Thread(target=self.worker, args=(
                self._instance_name, i, 'Server.Meteor.' + worker_name, cache, cache_opt, extra_queue))
            t.daemon = True
            t.start()
            self._threads.append(t)

    def launch_wait(self, waiting_on_stop=False):
        try:
            self.launch()
            self.wait()
        except KeyboardInterrupt:
            if __debug__:
                logger.info("Interrupt by Keyboard : Order to stop all thread")
            pass
        try:
            self.stop(waiting_on_stop)
        except KeyboardInterrupt:
            if __debug__:
                logger.info("Interrupt stop and wait by Keyboard : Unsafe stop ⇒ kill all thread")
            self.kill()

    def wait(self):
        # Wait the end of all thread
        for t in self._threads:
            t.join()

    def stop(self, waiting=False):
        for t in self._threads:
            t.w.stop()
        if waiting:
            self.wait()

    def kill(self):
        # for now, there is no way to kill a thread in python...
        # Unset daemon flags and raise a KeyboardInterrupt
        # Not Working :( thread active => can"t set daemon
        for t in self._threads:
            t.daemon = False
        raise KeyboardInterrupt("Killing all thread")

    def dump_requests_in_action(self):
        return [t.w.current_request for t in self._threads if t.isAlive()]

    def living_threads(self):
        return [t.isAlive() for t in self._threads]
