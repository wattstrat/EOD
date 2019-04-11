
import gridfs
from gridfs import GridIn
from DB.Mongo.Mongo import Mongo
from pymongo.database import Database
from pymongo.collection import Collection

"""
Those under two lines are just set for use the __main___ into this file
"""


"""
This class abstract the gridfs package.
GridFs is the MongoDB file system storage service.
It can store in Mongo database large objects or files.
"""


class GridFS(Mongo):

    """
            Initialization function
    """

    def __init__(self, database, collection='filesystem'):
        Mongo.__init__(self)
        if not isinstance(database, (Database, str)):
            raise TypeError(
                "GridFS error: database argument must be an instance of string or Database.")
        if not isinstance(collection, (Collection, str)):
            raise TypeError(
                "GridFS error: collection argument must be an instance of string or Collection.")

        self.set_database(database)
        self.set_collection(collection)
        object.__setattr__(self, "_gridfs", gridfs.GridFS(
            self.get_database(), self.get_collection_name()))
