

from sys import getsizeof
# from itertools import chain
# from collections import deque
# try:
#     from reprlib import repr
# except ImportError:
#     pass

if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class ElementMemoryError(MemoryError):
    pass


class SizedData(object):

    """
    Sized Data is an wrapper to an Data to add size of data
    i.e. permit to control the size of the object/element inserted.
    """

    def __init__(self, data, *args, **kwargs):
        """ Initialization function
        initial : possible internal cache values to be passed
        """
        super().__init__()

        self._data = data
        self._size = 0
        self._obj_size = {}
        self._check = []

    def get_val(self, varName, *args, **kwargs):
        return self._data.get_val(varName, *args, **kwargs)

    def in_cache(self, varName):
        return self._data.in_cache(varName)

    def rename(self, varName, newName):
        return self._data.rename(varName, newName)

    def set_val(self, varName, value, *args, **kwargs):
        """ Set varName: value to cache dictionnary. """
        objSize = SizedData.total_size(value) + SizedData.total_size(varName)
        # Compute new size
        newSize = self._size + objSize - self._obj_size.get(varName, 0)
        for check in self._check:
            check(self, varName, value, objSize, newSize)

        ret = self._data.set_val(varName, value, *args, **kwargs)
        self._size = newSize
        self._obj_size[varName] = objSize
        return ret

    def del_val(self, varName, *args, **kwargs):
        '''
        delete the variable varName from the cache dictionnary
        '''
        ret = self._data.del_val(varName, *args, **kwargs)
        self._size = self._size - self._obj_size[varName]
        del self._obj_size[varName]

    @staticmethod
    def total_size(o):
        return getsizeof(o)

    def __sizeof__(self):
        return self._size

    def __len__(self):
        return self._size

    def clear(self):
        self._data.clear()
        self._size = 0
        self._obj_size = {}

    def __getattr__(self, name):
        if name in self.__dict__:
            return self.__dict__[name]
        else:
            return getattr(self._data, name)

    # @staticmethod
    # def total_size(o, handlers={}):
    #     """
    #     Returns the approximate memory footprint an object and all of its contents.
    #     Automatically finds the contents of the following builtin containers and their subclasses:
    #     tuple, list, deque, dict, set and frozenset.
    #     To search other containers, add handlers to iterate over their contents:
    #     handlers = {SomeContainerClass: iter, OtherContainerClass: OtherContainerClass.get_elements}
    #     source: http://code.activestate.com/recipes/577504/
    #     """

    #     all_handlers = {tuple: iter, list: iter, deque: iter, dict: lambda d: chain.from_iterable(d.items()),
    #                     set: iter, frozenset: iter, }
    #     # user handlers take precedence track which object id's have already been seen
    #     all_handlers.update(handlers)
    #     seen = set()
    #     # estimate sizeof object without __sizeof__
    #     default_size = getsizeof(0)

    #     def sizeof(o):
    #         if id(o) in seen:       # do not double count the same object
    #             return 0
    #         seen.add(id(o))
    #         s = getsizeof(o, default_size)

    #         logger.debug("%s (repr: %s) => %d", type(o), repr(o), s)

    #         for typ, handler in all_handlers.items():
    #             if isinstance(o, typ):
    #                 s += sum(map(sizeof, handler(o)))
    #                 break
    #         return s

    #     return sizeof(o)

# ==== Idée en parcourant le code d'Aurélien ===
#
#
# import sys
# import numpy as np
# from pymongo import ASCENDING

# from Benchmarks.System.system import System
# from Dispatcher.dispatcher import Dispatcher

# from Data.Hypervisor.Politics.politics import Politic

# class PoliticsCache(Politic):
# 	"""
# 		This class represent one Hypervisor Politics.
# 		This politics preload all useful calcul datas on the computer RAM using Data/Cache class.
# 	"""

# 	MAX_MEMORY_USED_PERCENT = 90
# 	MIN_BYTES_MEMORY_TO_RUN = 2000000000

# 	def __init__(self, *args, **kwargs):
# 		""" Initialization function. """
# 		super().__init__(*args,**kwargs)
# 		self.system_infos = System()
# 		if self.system_infos.get_available_virtual_memory() < self.MIN_BYTES_MEMORY_TO_RUN:
# 			print("Server politic : The current host doen't appear to have enought memory ({0}) to run the program correctly."
#                             .format(self.MIN_BYTES_MEMORY_TO_RUN))
# 			sys.exit(0)

# 	def is_enought_space(self, bytes_to_allocated):
# 		"""
# 			Test if there are enought space in memory for allocated bytes_to_allocated.
# 			Return True it's possible, otherwise return false.
# 		"""
# 		memory_used_after_add = self.system_infos.get_used_virtual_memory() + bytes_to_allocated
# 		if memory_used_after_add <= self.system_infos.get_total_virtual_memory()/100*self.MAX_MEMORY_USED_PERCENT:
# 			return True
# 		return False

# 	def insert(self, data, data_name):
# 		if self.is_enought_space(data.__sizeof__()):
# 			self.cache.set(varName=data_name, value=data)
# 			return True
# 		return False


class SizedElementData(SizedData):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._max_size_of_element = kwargs.get("max_size_of_element", 0)
        if __debug__:
            logger.debug("Loading SizedElementData  with size %d", self._max_size_of_element)
        self._check.append(SizedElementData.checkElement)

    def checkElement(self, varName, value, objSize, newSize):
        if self._max_size_of_element == 0:
            return True
        if self._max_size_of_element < objSize:
            raise ElementMemoryError("%s: Maximum size of object is %d : object size : %d" %
                                     (varName, self._max_size_of_element, objSize))
        return True


class MaxSizedData(SizedData):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._max_size_of_data = kwargs.get("max_size_of_data", 0)
        if __debug__:
            logger.debug("Loading MaxSizedData  with size %d", self._max_size_of_data)
        self._check.append(MaxSizedData.checkDataSize)

    def checkDataSize(self, varName, value, objSize, newSize):
        if self._max_size_of_data == 0:
            return True
        if self._max_size_of_data < newSize:
            raise MemoryError("%s: Maximum size of Data is %d and current is %d => %d" %
                              (varName, self._max_size_of_data, self._size, newSize))
        return True


class maxSizedElementData(SizedElementData, MaxSizedData):
    pass
