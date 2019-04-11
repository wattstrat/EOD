import pymongo as PM


from DB.DB import DB
import Config.config as config

if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class Mongo(DB):

    """
    This class represent a MongoDB abstraction,
    using pymongo package.
    """

    MGC = None

    def __init__(self, *args, **kwargs):
        """
        This function initialize all Mongo variables.

        server_port: (Optional, default: 42).
        Represent mongodb server listening port.
        examples: 47, 8007...

        server_address: (Optional, default: localhost).
        Represent mongodb server address.
        examples: localhost, 127.0.0.1, 42.385.56.38...

        Set name and port variables, and initialize pymongo
        database, collection and client.
        To finish try to connect itself to mongodb server.
        """
        super().__init__(*args, **kwargs)
        if Mongo.MGC is None:
            server_port = kwargs.pop('server_port', config.MONGO_SERVER_PORT)
            server_address = kwargs.pop('server_address', config.MONGO_SERVER_ADDRESS)
            Mongo.MGC = Mongo.connect(server_address, server_port)
        self._server_port = kwargs.pop('server_port', config.MONGO_SERVER_PORT)
        self._server_address = kwargs.pop('server_address', config.MONGO_SERVER_ADDRESS)
        if __debug__:
            logger.debug(" DB.Mongo.mongo: server port = %s, server address = %s",
                         self._server_port, self._server_address)

        self._client = Mongo.MGC
        self._database = None
        self._strdatabase = None
        self._collection = None
        self._strcollection = None

        self.set_db_coll(**kwargs)

    @staticmethod
    def connect(host, port):
        """
        Try to connect to the client with the server.
        The server is represented by _server_address and _server_port.
        Return initialized client otherwise it return a basic pymongo
        client, with no connection.
        """
        return PM.MongoClient(host, port)

    def set_db_coll(self, **kwargs):
        database = kwargs.pop("database", None)
        collection = kwargs.pop("collection", None)
        if database is not None:
            self.set_database(database)
        if collection is not None:
            self.set_collection(collection)

    def set_database(self, database):
        """
        Try to set the client to another MongoDB database.
        database : Represent database name's or a pymongo database object.
        Return True if it succeed or False (and print a message) otherwise.
        """
        if not isinstance(database, (str, PM.database.Database)):
            if __debug__:
                logger.warning("DB_Mongo_set_database warning: database argument must be "
                               "a string or a pymongo Database instance.")
            return False
        if isinstance(database, str) & (self._strdatabase != database):
            self._database = PM.database.Database(self._client, database)
            self._strdatabase = database
            self._strcollection = str
        elif isinstance(database, PM.database.Database):
            if (self._strdatabase != database.name):
                self._database = database
                self._strdatabase = self._database.name
                self._strcollection = str
        return True

    def set_collection(self, collection):
        """
        Try to set the client to another MongoDB collection.
        collection : Represent collection name's or a pymongo Collection object.
        Return True if it succeed or False (and pritn a message) otherwise.
        """
        if not isinstance(collection, (str, PM.collection.Collection)):
            if __debug__:
                logger.warning("DB_Mongo_set_collection warning: collection argument must be "
                               "a string or Collection instance.")
            return False
        if isinstance(collection, (str)) & (self._strcollection != collection):
            self._collection = PM.collection.Collection(self._database, collection)
            self._strcollection = collection
        elif isinstance(collection, (PM.collection.Collection)):
            if (self._strcollection != collection.name):
                self._collection = collection
                self._strcollection = collection.name
        return True

    def _insert(self, document, **kwargs):
        """
        Try to insert a new MongoDB document in current collection.
        document : python dictionnary who represent new mongodb document.
        Return an OOID who represent created document id's or return False.
        """
        self.set_db_coll(**kwargs)
        return self._collection.insert_one(document)

    def _insert_many(self, **kwargs):
        """
        Try to insert a new MongoDB document in current collection.
        document : python dictionnary who represent new mongodb document.
        Return an OOID who represent created document id's or return False.
        """
        self.set_db_coll(**kwargs)
        documents = kwargs.get('documents')
        return self._collection.insert_many(documents)

    def _find(self, query, **kwargs):
        """
        Try to find some documents in MongoDB collection sets.
        query: python dictionnary who represent rules/query to find.
        Return a mongodb cursor with query results or False.
        """
        self.set_db_coll(**kwargs)
        # try:
        return self._collection.find(query, projection=kwargs.get('projection'), no_cursor_timeout=True)
        # except:
        #     logger.warning("DB_Mongo_find warning: An error occured during find. PLease retry !")
        #     return False

    def _update(self, query, update, **kwargs):
        """
        Try to update a document by another document.
        query : python dictionnary who represents the criterion to select documents to be updated in the collection.
        update : python dictionnary who represents how those documents should be modified.
        upsert : (Optional, default: False) Boolean, if True, a new document
        is created if no document matches query in the collection.
        By default only one document is updated.
        Return an OOID who represent the new document created or updated document id,
        or return False.
        """
        upsert = kwargs.pop("upsert", False)
        self.set_db_coll(**kwargs)
        if not isinstance(upsert, bool):
            if __debug__:
                logger.warning("DB_Mongo_update warning: upsert argument must be a bollean.")
            pass
        return self._collection.update_one(query, update, upsert=upsert)

    def _remove(self, query, **kwargs):
        """
        Try to find some documents in MongoDB collection sets.
        query: python dictionnary who represent rules/query to find.
        Return a mongodb cursor with query results or False.
        """
        self.set_db_coll(**kwargs)
        return self._collection.delete_one(query)

    def create_index(self, **kwargs):
        self.set_db_coll(**kwargs)
        varname = kwargs.get('indexkey', 'varname')
        return self._collection.create_index([(varname, PM.ASCENDING)], background=True)

    def insert(self, key=None, value=None, **kwargs):
        flag = kwargs.get('flag_raw_input')
        if flag:
            return self._insert_many(**kwargs)
        else:
            if key is not None:
                return self._insert({'key': key, 'value': value}, **kwargs)
            else:
                return self._insert(value, **kwargs)

    def update(self, key=None, value=None, query=None, **kwargs):
        if key is None and query is None:
            raise ValueError(
                "key and query are not defined. Please define one")
        if query is None:
            return self._update({'key': key}, value, **kwargs)
        else:
            # By default, if key and query present, just use query
            return self._update(query, value, **kwargs)

    def find(self, key=None, query=None, sort=None, **kwargs):
        if key is None and query is None:
            raise ValueError("key and query are not defined. Please define one")
        if query is None:
            val = self._find({'key': key}, **kwargs)
        else:
            # By default, if key and query present, just use query
            val = self._find(query, **kwargs)
        if sort is None or not isinstance(sort, tuple) or len(sort) != 2:
            if sort is not None:
                if __debug__:
                    logger.error("MongoDB find: sort is not a tuple of len 2. Discarding!")
                pass
            return val
        else:
            return val.sort(sort[0], sort[1])

    def delete(self, key=None, query=None, **kwargs):
        if key is None and query is None:
            raise ValueError("key and query are not defined. Please define one")
        if query is None:
            return self._remove({'key': key}, **kwargs)
        else:
            # By default, if key and query present, just use query
            return self._remove(query, **kwargs)

    def drop_collection(self, **kwargs):
        """
        Try to drop the current collection sets.
        Dropped collection is definitively trash and lost.
        Return True if it succeed or False.
        """
        self.set_db_coll(**kwargs)
        self._collection.drop()
        return True

    def rename_collection(self, new_name, **kwargs):
        """
        Try to drop the current collection sets.
        Dropped collection is definitively trash and lost.
        Return True if it succeed or False.
        """
        self.set_db_coll(**kwargs)
        self._collection.rename(new_name)
        return True

    def get_client(self):
        return self._client

    # def get_collection(self):
    #     """
    #         Return pymongo Collection object,
    #         representing the current collection set.
    #     """
    #     return self._collection

    # def get_collection_name(self):
    #     """
    #         Returne current collection name's.
    #     """
    #     return self._collection.name

    # def get_database_name(self):
    #     """
    #         Returned current database name's.
    #     """
    #     return self._database.name

    # def get_database(self):
    #     """
    #         Returne pymongo Database obect,
    #         representing the current database set.
    #     """
    #     return self._database

    # def get_client(self):
    #     """
    #         Return pymongo Client object, who represent
    #         the current connected client.
    #     """
    #     return self._client

    # def print_database(self):
    #     """
    #         Print the current MongoDB database name.
    #     """
    #     print("{0} is the current database".format(self._database.name))

    # def print_currentcol(self):
    #     """
    #         Print the current MongoDB collection name.
    #     """
    #     print("{0} is the current collection".format(self._collection.name))

    # def find_one(self, query, **kwargs):
    #     """
    #         Try to find only one document in MongoDB collection.
    #         query: python dictionnary who represent rules/query to find.
    #         Return a python dictionnary who represent the mongodb document
    #         or False.
    #     """
    #     try:
    #         return self._collection.find_one(query)
    #     except:
    #         print("DB_Mongo_find_one warning: An error occured during the find one function. PLease retry !")
    #         return False

    # def drop_collection(self):
    #     """
    #         Try to drop the current collection sets.
    #         Dropped collection is definitively trash and lost.
    #         Return True if it succeed or False.
    #     """
    #     try:
    #         self._collection.drop()
    #         return True
    #     except:
    #         print("DB_Mongo_drop_collection warning: Fail to drop {0}.".format(self.get_collection_name()))
    #         return False

    # def count_collection_documents(self, **kwargs):
    #     """
    #         Try to count documents in current collection set.
    #         Return the number of documents (int) or False.
    #     """
    #     try:
    #         return self.find().count()
    #     except:
    #         print("DB_Mongo_count_collection_documents warning: An error occured during {0} "
    #               "documents counting.".format(self.get_collection_name()))
    #         return False

    # def create_collection_index(self, variable_name, **kwargs):
    #     """
    #         This function create an index on collection documents.
    #         variable_name : String who represent the document key where index is created.
    #         database: (Optional). Database to set for apply index creation.
    #         collection: (Optional). Collection to set for apply index creation.
    #         direction: (Optional, default: pymongo.ASCENDING). Int who represent the
    #         direction of index (ASCENDING --> 1, DESCENDING --> -1).
    #         Retunr True if it succeed or False.
    #     """
    #     database = kwargs.pop("database")
    #     collection = kwargs.pop("collection")
    #     if not isinstance(database, str) or not isinstance(collection, str):
    #         raise ValueError("Weather_Stations_insert_distances_to_db error: "
    #                          "database and collection argument must be an instance of string.")
    #     if database:
    #         self.set_database(database)
    #     if collection:
    #         self.set_collection(collection)

    #     direction = kwargs.pop("direction", PM.ASCENDING)
    #     if not isinstance(direction, int):
    #         print("DB_Mongo_mongo_create_collection_index warning: direction argument must be an int, "
    #               "not {0}, this request will be ignored.".format(direction))
    #         return
    #     try:
    #         self._collection.create_index(variable_name, direction)
    #         return True
    # except: # Take pymongo error and log it and add another except to unknown error
    #         print("DB_Mongo_mongo_create_collection_index warning: Unknown error to create index "
    #               "to {0}, into {1} collection.".format(variable_name, self.get_collection_name()))
    #         return False
