from copy import deepcopy
import numpy as np
import random
import pickle
import json
from pymongo import UpdateOne, ASCENDING

import Config.config as config
from Calculus.calculus import Calculus
from DB.Mongo.Mongo import Mongo
from babel.dot._auto_parameters_definition import auto_parameters_definition as auto
from Utils.progress_bar import printProgress

if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class ValidationError(SyntaxError):

    def __init__(self, *args, **kwargs):
        SyntaxError.__init__(self, *args, **kwargs)


class PerformInsertion(Calculus):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.to_run = ('Init.Demand.Transport',
                       'Init.Demand.Tertiary',
                       'Init.Demand.Residential',
                       'Init.Supply.Heatgrid',
                       'Init.Demand.Agriculture',
                       'Init.Supply.Capas',
                       'Init.Demand.Industry',
                       )
        self.default_fields = {'metadata': {},
                               'unit': '',
                               'operation_type': ('mean', '')}

        self._kwargsInitialiser = {}

        if "init_db" in kwargs:
            self._kwargsInitialiser["init_db"] = kwargs["init_db"]

        if "init_collection" in kwargs:
            self._kwargsInitialiser["init_collection"] = kwargs["init_collection"]

        self.initialiser = self.calculus(
            'Calculus.Initialisation.AsyncInit.asyncinit_entrypoint.Initialiser', **self._kwargsInitialiser)

    def _run(self):
        self.initialiser._mongo.drop_collection()
        # only industry, change later to all classes
        for idx, onecalc in enumerate(self.to_run):
            inst = self.calculus(onecalc, **self._kwargsInitialiser)
            status = inst()
            if idx == 0:
                self.initialiser._mongo.create_index(indexkey='geocode_insee')
        self.initialiser._mongo.create_index(indexkey='geocode_insee')
        temp = self.check_missing()
        return temp

    def check_missing(self):
        with open('babel/dot/config_tags.json', 'r') as f:
            ctags = json.load(f)
        refdict = self.initialiser._mongo.find(query={'geocode_insee': 'FR99999'})
        totdict = {}
        for onetag, val in ctags.items():
            paramname = val[0]
            if paramname not in refdict[0]:
                print('Missing %s in computed config async, use auto_parameters_definition' % (paramname))
                sector = '_'.join(paramname.split('_')[:3])
                categ = paramname.split('_')[3]
                if 'Transport' in sector:
                    if categ == 'Consumption':
                        categ = '_'.join(paramname.split('_')[3:5])
                defdict = self.initialiser.searcher(sector, categ)
                subdict = defdict[paramname].copy()
                for key in self.default_fields:
                    if key not in subdict:
                        subdict[key] = self.default_fields[key]
                tempdict = {paramname: subdict}
                totdict.update(tempdict)
        if totdict:
            self.initialiser._mongo.update(query={'geocode_insee': 'FR99999'}, value={'$set': totdict})
        return totdict


class Initialiser(Calculus):
    '''
    methode def _compute()
    chaque classe dans les sous fichiers renvoie
    - un dictionnaire de geocode de variable de type
    {'FR99999':{
                'Demand_Transport_Freight_Consumption_boat_efficiency_electricitygrid':{
                        'min':0,                                    *
                        'max':100,                                  *
                        'default':43.2,                             *
                        'unit':'kWh',                               *
                        'operation_type':('mean', ''),              * (mean, fieldname)
                        'type':'abs_val',                           *
                        'metadata': { ce qu'on veut, au moins fieldname si fieldname is not None
                                     key: (val, type)               * val : string, value
        type : True - to be kept
               'sum' - the field is the same for every subdict, put it in counties, sums the values
               False - the field is not to be put in counties
               string - the field is to be put in counties by performing an operation coded by the string
                    (sum values, mean, variable name to perform implicit weighted average, etc)
                                    },                              * if fieldname!='' it needs to be in metadata
                        }
                }
    }
    * : obligatoire
    ----
    supported operation types :
    + 'mean' : perform a simnple unweighted mean of the communes values to obtain departement and france
    + 'surface_mean' : mean weighted by communes' surfaces in km2
    + 'population_mean' : mean weighted by communes' population
    + 'sum' : sums the values to obtain the value of the group

    ----TODO
    - validation fieldname
    - same variables


    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.required_fields = ['min', 'max', 'default',
                                'unit', 'operation_type', 'type', 'metadata']
        self.fixed_fields = ['unit', 'type', 'operation_type']
        self.fields_to_agg = set(self.required_fields) - \
            set(self.fixed_fields) - set({'metadata'})
        self.geo_list = self._cache.get_val('geocodes')
        self.geocodes = {geocode: {} for geocode in self.geo_list}
        self.geo_indexes = self._cache.get_val('geocodes_indexes')
        self.counties_indexes = self._cache.get_val('counties_indexes')
        if "init_db" in kwargs:
            self._init_db = kwargs["init_db"]
        else:
            self._init_db = config.MONGODB_INIT_DB

        if "init_collection" in kwargs:
            self._init_collection = kwargs["init_collection"]
        else:
            self._init_collection = config.__INIT_COLLECTIONS__['main']
        self._mongo = Mongo(database=self._init_db,
                            collection=self._init_collection)

    def _run(self):
        mydict = self._compute()
        self.validate(mydict)
        totdict = self.compute_fr_counties(mydict)
        totdocs = []
        for key, val in totdict.items():
            tempdict = {'geocode_insee': key}
            tempdict.update(val)
            totdocs.append(tempdict)
        self.bulk_insertion(totdocs)
        return True

    def bulk_insertion(self, totdocs):
        ndocs_batch = int(1024 * 1024 * 16 /
                          len(pickle.dumps(json.dumps(totdocs[0]))) / 2)
        operations = []
        for idx, doc in enumerate(totdocs):
            printProgress(idx, len(totdocs), prefix='Class %s' %
                          (self.__class__.__name__))
            operations.append(
                UpdateOne({'geocode_insee': doc['geocode_insee']}, {'$set': doc}, upsert=True))
            if len(operations) == ndocs_batch:
                self._mongo._collection.bulk_write(operations, ordered=False)
                operations = []
        self._mongo._collection.bulk_write(operations, ordered=False)
        return True

    def compute_fr_counties(self, mydict):
        myvars = list(mydict[self.geo_list[0]].keys())
        ret = {county: {myvar: {} for myvar in myvars}
               for county in self.counties_indexes}
        mykeys_meta = {key: val for key, val in mydict[self.geo_list[0]][myvars[0]]['metadata'].items()
                       if isinstance(val, tuple) and val[1]}
        for county in self.counties_indexes:
            for myvar in myvars:
                ret[county][myvar] = self.aggregating_fct(
                    mydict, county, myvar)
        self.validate(ret)
        self.renormalize_sum_max(mydict, ret)
        mydict.update(ret)
        return mydict

    def renormalize_sum_max(self, mydict, ret):
        onegeo = random.choice(list(mydict.keys()))
        myvars = list(mydict[onegeo].keys())
        for myvar in myvars:
            aggmethod = mydict[onegeo][myvar]['operation_type']
            if aggmethod[0] == 'sum':
                for county in ret:
                    ret[county][myvar]['max'] = ret['FR99999'][
                        myvar]['default'] * aggmethod[1]
        return True

    def aggregating_fct(self, mydict, county, myvar):
        county_composition = self.geo_list[self.counties_indexes[
            county]['start']:self.counties_indexes[county]['end']]
        aggmethod = mydict[county_composition[0]][myvar]['operation_type']
        ret = {key: {'val': [], 'weights': []} for key in self.fields_to_agg}
        for geocode in county_composition:
            for key in self.fields_to_agg:
                ret[key]['val'].append(mydict[geocode][myvar][key])
                if aggmethod[0] == 'mean':
                    if aggmethod[1]:
                        ret[key]['weights'].append(mydict[geocode][myvar][
                                                   'metadata'][aggmethod[1]][0])
                    else:
                        ret[key]['weights'].append(1)
        ret = {key: {'val': np.array(ret[key]['val']), 'weights': np.array(
            ret[key]['weights'])} for key in ret}
        if aggmethod[0] == 'sum':
            agg_ret = {key: float(ret[key]['val'].sum()) for key in ret}
            agg_ret
        elif aggmethod[0] == 'mean':
            weights = ret[key]['weights']
            if weights.sum() == 0:
                weights = np.ones(weights.shape)
            agg_ret = {key: float(np.average(ret[key]['val'], weights=weights)) for key in ret}
        else:
            raise Exception

        # metadata construction for counties
        mymeta = mydict[county_composition[0]][myvar]['metadata']
        metatemp = {key: {'val': [], 'weights': [], 'type': None} for key in mymeta
                    if mydict[county_composition[0]][myvar]['metadata'][key][1]}
        for geocode in county_composition:
            for key in metatemp:
                vartemp = mydict[geocode][myvar]['metadata'][key][1]
                if vartemp == 'sum':
                    metatemp[key]['val'].append(
                        mydict[geocode][myvar]['metadata'][key][0])
                    metatemp[key]['type'] = vartemp
                elif isinstance(vartemp, str):
                    metatemp[key]['val'].append(
                        mydict[geocode][myvar]['metadata'][key][0])
                    metatemp[key]['weights'].append(
                        mydict[geocode][myvar]['metadata'][vartemp][0])
                    metatemp[key]['type'] = vartemp
                elif vartemp is True:
                    metatemp[key] = mydict[geocode][myvar]['metadata'][key]
        interm_meta = metatemp
        metatemp = {key: {'val': np.array(metatemp[key]['val']), 'weights': np.array(metatemp[key]['weights'])}
                    for key in metatemp if 'val' in metatemp[key]}
        for key in interm_meta:
            if 'type' in interm_meta[key]:
                metatemp[key]['type'] = interm_meta[key]['type']

        agg_meta = {}
        for key in metatemp:
            if 'weights' in metatemp[key] and metatemp[key]['weights']:
                agg_meta[key] = (float(np.average(metatemp[key]['val'], weights=metatemp[key]['weights'])),
                                 metatemp[key]['type'])
            elif 'weights' in metatemp[key]:
                agg_meta[key] = (
                    float(metatemp[key]['val'].sum()), metatemp[key]['type'])
            else:
                agg_meta[key] = metatemp[key]
        agg_ret.update({key: mydict[county_composition[0]][
                       myvar][key] for key in self.fixed_fields})
        agg_ret.update({'metadata': agg_meta})
        return agg_ret

    def validate(self, mydict):
        self.validate_nvars(mydict)
        self.validate_fieldname(mydict)
        for myfield in self.fixed_fields:
            self.validate_reqfield_val(mydict, myfield)
        self.validate_required_fields(mydict)
        self.validate_metadata(mydict)
        self.validate_field_types(mydict, 'operation_type', tuple)

    def validate_metadata(self, mydict):
        onegeo = random.choice(list(mydict.keys()))
        myvars = list(mydict[onegeo].keys())
        mykeys_meta = {myvar: {} for myvar in myvars}
        for myvar in myvars:
            for key, val in mydict[onegeo][myvar]['metadata'].items():
                if isinstance(val, tuple) and val[1]:
                    mykeys_meta[myvar][key] = val

        for geocode in mydict:
            for myvar in myvars:
                for key, val in mykeys_meta[myvar].items():
                    mymeta = mydict[geocode][myvar]['metadata']
                    if set(mydict[onegeo][myvar]['metadata'].keys()) != set(mymeta):
                        raise ValidationError('Metadata dont have the same fields for '
                                              'for geocodes %s and %s, variable %s. Fields are %s and %s' %
                                              (onegeo, geocode, myvar,
                                               set(mydict[onegeo][myvars[0]][
                                                   'metadata'].keys()),
                                               set(mymeta)))
                    if val[1] == 'sum':
                        if key in mymeta:
                            pass
                        else:
                            raise ValidationError('Field %s in metadata is coded as the same across geocodes and vars, '
                                                  'false for geocodes %s and %s, variable %s' %
                                                  (key, onegeo, geocode, myvar))
                    elif val[1] is True:
                        if key in mymeta and mymeta[key][0] == val[0]:
                            pass
                        else:
                            raise ValidationError('Field %s in metadata is coded as the same across geocodes and vars, '
                                                  'false for geocodes %s and %s, variable %s' %
                                                  (key, onegeo, geocode, myvar))
                    else:
                        if val[1] not in mymeta:
                            raise ValidationError('Field %s missing in metadata '
                                                  'for geocode %s and variable %s' %
                                                  (val[1], geocode, myvar))
                        elif mymeta[key][1] not in mymeta:
                            raise ValidationError('Field %s missing in metadata '
                                                  'for geocode %s and variable %s' %
                                                  (mymeta[key][1], geocode, myvar))
                        elif mymeta[key][1] != val[1]:
                            raise ValidationError('Field %s does not have the same aggregation rule '
                                                  'for geocodes %s and %s, variable %s. Rules are %s and %s resp.' %
                                                  (key, onegeo, geocode, myvar, val[1], mymeta[key][1]))
                        else:
                            pass
                for key in mydict[geocode][myvar]['metadata']:
                    if not isinstance(mydict[geocode][myvar]['metadata'][key][0], str):
                        mydict[geocode][myvar]['metadata'][key] = (float(mydict[geocode][myvar]['metadata'][key][0]),
                                                                   mydict[geocode][myvar]['metadata'][key][1])
        return True

    def validate_required_fields(self, mydict):
        onegeo = random.choice(list(mydict.keys()))
        myvars = list(mydict[onegeo].keys())
        for geocode in mydict:
            for myvar in myvars:
                for req_var in self.required_fields:
                    if req_var not in mydict[geocode][myvar]:
                        raise ValidationError('Field %s is missing from geocode %s and variable %s' %
                                              (req_var, geocode, myvar))
                    if req_var in self.fields_to_agg:
                        mydict[geocode][myvar][req_var] = float(
                            mydict[geocode][myvar][req_var])
        return True

    def validate_nvars(self, mydict):
        onegeo = random.choice(list(mydict.keys()))
        nb_var = len(mydict[onegeo])
        for key in mydict:
            if len(mydict[key]) != nb_var:
                raise ValidationError('%s and %s do not have the same variables, %s != %s' %
                                      (onegeo, key, nb_var, len(mydict[key])))
        return True

    def validate_fieldname(self, mydict):
        onegeo = random.choice(list(mydict.keys()))
        myvars = list(mydict[onegeo].keys())
        mytypes = {key: mydict[onegeo][key]['operation_type']
                   for key in myvars}
        for geocode in mydict:
            for myvar in myvars:
                mytype = mydict[geocode][myvar]['operation_type']
                if mytype != mytypes[myvar]:
                    raise ValidationError('For var %s, %s and %s do not have the same operation_type' %
                                          (myvar, onegeo, geocode))
                tempbool = mytype[1] not in mydict[geocode][myvar]['metadata']
                if mytype[0] != 'sum' and mytype[1] and tempbool:
                    raise ValidationError('For var %s, and geocode %s, fieldname %s is not in metadata' %
                                          (myvar, geocode, mytype[1]))
        return True

    def validate_reqfield_val(self, mydict, myfield):
        onegeo = random.choice(list(mydict.keys()))
        myvars = list(mydict[onegeo].keys())
        mytypes = {key: mydict[onegeo][key][myfield] for key in myvars}
        for geocode in mydict:
            for myvar in myvars:
                if mydict[geocode][myvar][myfield] != mytypes[myvar]:
                    raise ValidationError('For var %s, %s and %s do not have the same field %s' %
                                          (myvar, onegeo, geocode, myfield))
        return True

    def validate_field_types(self, mydict, field, mytype):
        onegeo = random.choice(list(mydict.keys()))
        myvars = list(mydict[onegeo].keys())
        for geocode in mydict:
            for myvar in myvars:
                if not isinstance(mydict[geocode][myvar][field], mytype):
                    raise ValidationError('For var %s, geocode %s, %s is not a %s' %
                                          (myvar, geocode, field, mytype))
        return True

    def _compute(self):
        raise NotImplementedError

    def searcher(self, section, category, subcat=None):
        myfields = ['min', 'max', 'default', 'type']
        myfields_inpack = ['min', 'max', 'default']
        myfields_outpack = ['type']
        for cat in auto[section]['categories']:
            if cat['name'] == category:
                subdict = deepcopy(cat)
                break
        else:
            raise Exception(
                'Category %s was not found in section %s' % (category, section))
        ret = {}
        for hypo in subdict['hypotheses']:
            for subcateg in hypo['subcategories']:
                if subcat is None or subcateg['name'] == subcat:
                    if 'parameter' in hypo:
                        paramtype = 'parameter'
                        if 'pack' in hypo[paramtype]:
                            for parameter in hypo[paramtype]['pack']:
                                varname = '_'.join([section, category, subcateg['name'], hypo[
                                                   paramtype]['name'], parameter['name']])
                                subfields = [key for key, bool1 in zip(
                                    myfields_inpack, [key in parameter for key in myfields_inpack]) if bool1]
                                ret[varname] = {key: parameter[key]
                                                for key in subfields}
                                subfields2 = [key for key, bool1 in zip(
                                    myfields_outpack, [key in hypo[paramtype] for key in myfields_outpack]) if bool1]
                                ret[varname].update(
                                    {key: hypo[paramtype][key] for key in subfields2})
                                if __debug__:
                                    if set(myfields) - set(subfields) - set(subfields2):
                                        logger.warning('The set of fields %s is missing from section %s, '
                                                       'category %s, subcategory %s and parameter %s'
                                                       % (set(myfields) - set(subfields), section, category,
                                                          subcateg['name'], parameter['name']))
                        else:
                            varname = '_'.join([section, category, subcateg[
                                               'name'], hypo[paramtype]['name']])
                            subfields = [key for key, bool1 in zip(
                                myfields, [key in hypo[paramtype] for key in myfields]) if bool1]
                            ret[varname] = {key: hypo[paramtype][key]
                                            for key in subfields}
                            if __debug__:
                                if set(myfields) - set(subfields):
                                    logger.warning('The set of fields %s is missing from section %s,'
                                                   ' category %s, subcategory %s and parameter %s'
                                                   % (set(myfields) - set(subfields), section, category,
                                                      subcateg['name'], hypo[paramtype]['name']))
                    elif 'parametersGroup' in hypo:
                        paramtype = 'parametersGroup'
                        for group in hypo[paramtype]:
                            if 'pack' in group:
                                for parameter in group['pack']:
                                    varname = '_'.join([section, category, subcateg['name'],
                                                        group['name'], parameter['name']])
                                    subfields = [key for key, bool1 in zip(
                                        myfields_inpack, [key in parameter for key in myfields_inpack]) if bool1]
                                    ret[varname] = {key: parameter[key]
                                                    for key in subfields}
                                    subfields2 = [key for key, bool1 in zip(
                                        myfields_outpack, [key in group for key in myfields_outpack]) if bool1]
                                    ret[varname].update(
                                        {key: group[key] for key in subfields2})
                                    if __debug__:
                                        if set(myfields) - set(subfields) - set(subfields2):
                                            logger.warning('The set of fields %s is missing from section %s, '
                                                           'category %s, subcategory %s and parameter %s'
                                                           % (set(myfields) - set(subfields), section, category,
                                                              subcateg['name'], parameter['name']))
                            else:
                                varname = '_'.join(
                                    [section, category, subcateg['name'], group['name']])
                                subfields = [key for key, bool1 in zip(
                                    myfields, [key in group for key in myfields]) if bool1]
                                ret[varname] = {key: group[key]
                                                for key in subfields}
                                if __debug__:
                                    if set(myfields) - set(subfields):
                                        logger.warning('The set of fields %s is missing from section %s,'
                                                       ' category %s, subcategory %s and parameter %s'
                                                       % (set(myfields) - set(subfields), section, category,
                                                          subcateg['name'], group['name']))

        return ret

    def filter_varname(self, mydict, mystring):
        ret = {}
        for key in mydict:
            if mystring in key:
                ret.update({key: mydict[key]})
        return ret

    def find_idx(self, varname, liststrings):
        ret = []
        for onelist in liststrings:
            for onestr in onelist:
                if onestr in varname:
                    ret.append(onelist.index(onestr))
                    break
        return ret
