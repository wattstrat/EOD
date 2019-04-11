from DB.Mongo.Mongo import Mongo as MongoDB
from Data.DB.db import DB

import pickle
import math
import Config.config as config

if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class Mongo(MongoDB, DB):

    '''
            This class is going to deal with a Mongo database.
    '''

    def __init__(self, *args, **kwargs):
        '''
            Initialize class variables.
        '''
        super().__init__(*args, **kwargs)
        self._ooiddict = kwargs.get('ooiddict', {})
        self._sizelimit = config.__PICKLE_THRESHOLD__

    def in_cache(self, varName):
        query = {'variable': varName}
        tempcursor = self._find(query)
        return tempcursor.count() == 1

    def rename(self, varName, newName):
        query = {'variable': varName}
        self._update(query, {"$set": {'variable': newName}})

    def set_val(self, varName, value, *args, **kwargs):
        '''
        abstract method, to be passed to method insert of DB.Mongo.mongo
        inserts document in Mongo
        '''
        if __debug__:
            logger.debug('Setting DB Mongo var %s with %s', varName, value)
        DB.set_val(self, varName, value, *args, **kwargs)
        # Debug WARN if dev change database/collection in the DataCache and
        # change_db_assumed not true
        if ('database' in kwargs or 'collection' in kwargs) and not kwargs.get('change_db', False):
            if __debug__:
                logger.warning('set_val: Changing database or collection for the Mongo Cache : '
                               'PERMANENT change. Disable warning by setting change_db=True')
            pass

        pickled_val = pickle.dumps(value)
        temp = []
        nitems = math.floor(len(pickled_val) / self._sizelimit) + 1
        for i in range(nitems):
            idx_ini = i * self._sizelimit
            idx_end = (i + 1) * self._sizelimit
            temp = pickled_val[idx_ini: min(idx_end, len(pickled_val))]
            tempupdate = self._update({'variable': varName, 'part': i, 'len': nitems}, {
                '$set': {'value': temp,
                         '_metadata': self._metadata.get(varName)}},
                                      upsert=True, **kwargs)
            if tempupdate.upserted_id is not None:
                if __debug__:
                    logger.debug('Mongo.set_val: inserted document for variable = %s', varName)
                if varName in self._ooiddict:
                    self._ooiddict[varName].append(tempupdate.upserted_id)
                else:
                    self._ooiddict[varName] = [tempupdate.upserted_id]
            else:
                if __debug__:
                    logger.debug('Mongo.set_val: updated document for variable = %s, part = %s', varName, i)
                pass
        return value

    def get_val(self, varName, *args, **kwargs):
        '''
        This function gets one or more objects from a specific Mongo database and collection and returns them.
        query : Mongo request.
        '''
        if __debug__:
            logger.debug('Getting DB Mongo var %s', varName)
        DB.get_val(self, varName, *args, **kwargs)

        # Debug WARN if dev change database/collection in the DataCache and
        # change_db_assumed not true
        if ('database' in kwargs or 'collection' in kwargs) and not kwargs.get('change_db', False):
            if __debug__:
                logger.warning('get_val: Changing database or collection for the Mongo Cache : '
                               'PERMANENT change. Disable warning by setting change_db=True')
            pass

        query = {'variable': varName}
        tempcursor = self._find(query, **kwargs)
        count = tempcursor.count()
        if count == 0:
            if __debug__:
                logger.debug('Mongo.get_val: No document found for variable = %s', varName)
            raise KeyError(varName, ' is not a valid key')
        nitems = tempcursor[0]['len']
        if count != nitems:
            # Debug only
            if __debug__:
                logger.info('%s degraded: not all part saved : Saved(%d), Get(%d)', varName, count, nitems)
            for elmt in tempcursor:
                if __debug__:
                    logger.info("part: %d / type : %s / OOID", elmt['part'], type(elmt['value']), elmt['_id'])
                raise KeyError(varName, ' is degraded: not all part saved : Saved(%d), Get(%d)' % (count, nitems))

        try:
            multi_val = [b''] * nitems
            present = [False] * nitems
            for elmt in tempcursor:
                # logger.info("part: %d / type : %s", tempcursor[i]['part'],type(tempcursor[i]['value']))
                multi_val[elmt['part']] = elmt['value']
                present[elmt['part']] = True
            if not all(present):
                raise KeyError(varName, ' is degraded: not all part present : %s' % (present))
            myjoined = b''.join(multi_val)
            try:
                val = pickle.loads(myjoined)
            except pickle.UnpicklingError:
                raise KeyError(varName, " is corrupted: couldn't unpickle it")
            return val
        except KeyError:
            if __debug__:
                logger.debug('Mongo.get_val: More than one document found for variable = %s', varName)
            raise KeyError(varName, ' is not a valid key')

    def del_val(self, varName, *args, **kwargs):
        '''
        This function delete a variable name
        query : Mongo request.
        '''
        if __debug__:
            logger.debug('Deletting DB Mongo var %s', varName)
        DB.del_val(self, varName, *args, **kwargs)

        # Debug WARN if dev change database/collection in the DataCache and
        # change_db_assumed not true
        if ('database' in kwargs or 'collection' in kwargs) and not kwargs.get('change_db', False):
            if __debug__:
                logger.warning('del_val: Changing database or collection for the Mongo Cache : '
                               'PERMANENT change. Disable warning by setting change_db=True')
            pass

        query = {'variable': varName}
        tempfind = self._find(query, **kwargs)
        if tempfind.count() > 1:
            if __debug__:
                logger.debug('More than 1 result when looking for %s in DB', query)
            pass
        return self._remove(query, **kwargs)

    def clear(self):
        '''
        clear all the value stored
        '''
        if __debug__:
            logger.debug('Clearing DB Mongo')
        DB.clear(self)
        self._ooiddict = {}
        self._cache_dict = {}
        self.drop_collection()

    # def updateVal(self, query, newVal, *args, **kwargs):
    #     '''
    #     finds documents matching query and changes their value to  newVal
    #     '''
    #     return self.update(query, newVal, **kwargs)
