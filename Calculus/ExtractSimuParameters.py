import re
import numpy as np
from copy import deepcopy
import pymongo

import Config.config as config

from Calculus.calculus import Calculus
from DB.Mongo.Mongo import Mongo
from Utils.dict_manipulations import flatten
from Calculus.CalcVar import CalcVar
from Utils.Numpy import div0


if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class ExtractSimulationParameters(Calculus):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Always skip hash/cache because we return custom param matrix
        self._skip_cache = True
        self._skip_hash = True

    def _run(self, request, milestones_date, **kwargs):
        # Extract value in dict for simulation and construct initial param matrix
        if __debug__:
            logger.info('Extracting Parameters')

        extractMilestoneParam = self.calculus('Simulation.ExtractSimulationMilestoneParameters')
        milestones = request['parameters']
        default_vals = self.calculus('Simulation.DefaultValues', simu_specific=True)
        simu_defaults, pct_rep_w = self.get_variable(default_vals(request['default_values'], request['parameters']))
        self.simdef = simu_defaults
        self.pctrepw = pct_rep_w

        ret = {}
        simu_territory_groups = {}
        milestones = milestones + [{}] * (len(milestones_date) - len(milestones))
        for ind, milestone in enumerate(milestones):
            milestone_date = milestones_date[ind]
            paramsMilestoneSimu = extractMilestoneParam(milestone, milestone_date, simu_defaults[ind], pct_rep_w)
            vParamsMilestoneSimu = self.get_variable(paramsMilestoneSimu)
            # terr_groups = self.get_variable(vParamsMilestoneSimu['territory_groups'])
            # simu_territory_groups.update(terr_groups)
            hypos = vParamsMilestoneSimu['param_matrix']
            for hypo, mat in hypos.items():
                if hypo in ret:
                    ret[hypo].append(mat)
                else:
                    ret[hypo] = [mat]
        return {'territory_groups': simu_territory_groups, 'param_matrix': ret}


class DefaultValues(Calculus):
    '''
    gerer subgroup avec abs_val
    ajouter percent_repartition
    '''

    def __init__(self, *args, **kwargs):
        '''
        '''
        super().__init__(*args, **kwargs)
        self.def_mat = self._cache.get_val('Hypothesis:Default').copy()
        self.tot_order = self._cache.get_val('Hypothesis:Default:Order').copy()
        self.geo_idx = self._cache.get_val('geocodes_indexes')
        self.cty_idx = self._cache.get_val('counties_indexes')
        self.def_types = self._cache.get_val('Hypothesis:Default:Types')
        self.set_percent_repartition = {}
        self.geocodes = self._cache.get_val('geocodes')
        self._mongo = Mongo(database=config.MONGODB_INIT_DB, collection=config.__INIT_COLLECTIONS__['main'])
        self.pct_rep_weights = {}

    def _run(self, def_vals, parameters):
        '''
        '''
        self.def_vals = def_vals
        ret = []
        for paramM in parameters:
            self.update_default_oneMilestone(paramM, mytype='values')
            self.update_default_oneMilestone(paramM, mytype='subgroup')
            self.build_percent_repartitions()
            ret.append(self.def_mat.copy())
        return ret, self.pct_rep_weights

    def update_default_oneMilestone(self, paramM, mytype='values'):
        '''
        '''
        storage = {}
        for sector in paramM:
            for categ in paramM[sector]:
                sector_name = sector + '_' + categ['category']
                storage[sector_name] = {}
                for terrgroup in categ['territory_groups']:
                    if mytype == 'values':
                        self.terrgroup_update(sector_name, terrgroup, categ, storage)
                    if mytype == 'subgroup':
                        self.subgroup_update(sector_name, terrgroup, categ, storage)
        for sector_name in storage:
            self.update_oneparam_geo(sector_name, storage[sector_name])

    def build_percent_repartitions(self):
        for sector_name, params in self.set_percent_repartition.items():
            self.pct_rep_weights[sector_name] = {}
            tempcalc = CalcVar(None, self.def_mat[sector_name], random_name=True)
            mymat = self.get_variable(tempcalc).copy()
            for param_name in params:
                self.default_from_db(sector_name, param_name, mymat)
            tempmat = CalcVar(None, mymat, random_name=True)
            tempmat.sync_cache(self._cache, remote=True)
            self.def_mat[sector_name] = tempmat.name

    def default_from_db(self, sector_name, param_name, mymat):
        idx = self.tot_order[sector_name][param_name]

        query = {'geocode_insee': {'$in': list(self.cty_idx.keys())}}
        proj = {'geocode_insee': 1, sector_name + '_' + param_name: 1}
        sort = ('geocode_insee', pymongo.DESCENDING)
        docs = self._mongo.find(query=query, projection=proj, sort=sort)
        for doc in docs:
            idxini = self.cty_idx[doc['geocode_insee']]['start']
            idxend = self.cty_idx[doc['geocode_insee']]['end']
            val = doc[sector_name + '_' + param_name]['default']
            if val == 0:
                val = config.NONZERO_VAL
            mymat[idxini:idxend, idx] = val

        query = {'geocode_insee': {'$in': self.geocodes}}
        proj = {'geocode_insee': 1, sector_name + '_' + param_name: 1}
        docs = self._mongo.find(query=query, projection=proj)
        fieldname = None
        if docs[0][sector_name + '_' + param_name]['operation_type'][1]:
            fieldname = docs[0][sector_name + '_' + param_name]['operation_type'][1]
        else:
            fieldname = 'Population du territoire'
        self.pct_rep_weights[sector_name][param_name] = np.ones((len(self.geocodes),))
        if docs.count() != len(self.geocodes):
            raise
        for doc in docs:
            val = doc[sector_name + '_' + param_name]['default']
            if val == 0:
                val = config.NONZERO_VAL
            mymat[self.geo_idx[doc['geocode_insee']], idx] = val
            if fieldname:
                mygeoidx = self.geo_idx[doc['geocode_insee']]
                tempname = sector_name + '_' + param_name
                self.pct_rep_weights[sector_name][param_name][mygeoidx] = doc[tempname]['metadata'][fieldname][0]

    def param_name_builder(self, prefix, val_dict, list_init):
        for key, val in val_dict.items():
            if isinstance(val, dict):
                self.param_name_builder(prefix + '_' + key, val, list_init)
            else:
                param_name = prefix + '_' + key
                list_init.append(param_name)

    def terrgroup_update(self, sector_name, terrgroup, categ, storage):
        '''
        '''
        list_init = []
        if 'values' in terrgroup:
            self.param_name_builder(categ['subcategory'], terrgroup['values'], list_init)
            for param_name in list_init:
                if self.def_types[sector_name][param_name] == 'percent_repartition':
                    if sector_name in self.set_percent_repartition:
                        self.set_percent_repartition[sector_name].update({param_name})
                    else:
                        self.set_percent_repartition[sector_name] = {param_name}
                else:
                    default_terr = self.compute_default_terrgroup(sector_name, param_name, terrgroup)
                    tempdict = {geo: default_terr for geo in terrgroup['geocodes']}
                    if param_name in storage[sector_name]:
                        storage[sector_name][param_name].update(tempdict)
                    else:
                        storage[sector_name][param_name] = tempdict

    def subgroup_update(self, sector_name, terrgroup, categ, storage):
        '''
        '''
        if 'subgroup' in terrgroup:
            for geo in terrgroup['subgroup']:
                list_init = []
                self.param_name_builder(categ['subcategory'], terrgroup['subgroup'][geo]['values'], list_init)
                for param_name in list_init:
                    if self.def_types[sector_name][param_name] == 'percent_repartition':
                        if sector_name in self.set_percent_repartition:
                            self.set_percent_repartition[sector_name].update({param_name})
                        else:
                            self.set_percent_repartition[sector_name] = {param_name}
                    else:
                        default_terr = self.compute_default_terrgroup(sector_name, param_name, terrgroup)
                        tempdict = {geo: default_terr}
                        if param_name in storage[sector_name]:
                            storage[sector_name][param_name].update(tempdict)
                        else:
                            storage[sector_name][param_name] = tempdict

    def update_oneparam_geo(self, sector_name, mydict):
        '''
        '''
        tempcalc = CalcVar(None, self.def_mat[sector_name], random_name=True)
        mymat = self.get_variable(tempcalc).copy()
        for param_name in mydict:
            idx = self.tot_order[sector_name][param_name]
            if self.def_types[sector_name][param_name] != 'abs_val':
                for geo in sorted(mydict[param_name].keys(), reverse=True):
                    val = mydict[param_name][geo]
                    # cope with 0, as we have ratios, to avoid neutral element initialisation
                    if self.def_types[sector_name][param_name] == 'percent_repartition' and val == 0:
                        val = config.NONZERO_VAL
                    if geo in self.cty_idx:
                        idxini = self.cty_idx[geo]['start']
                        idxend = self.cty_idx[geo]['end']
                        mymat[idxini:idxend, idx] = val
                    else:
                        mymat[self.geo_idx[geo], idx] = val
            else:
                mymat[:, idx] = np.zeros(mymat[:, idx].shape)
                # for geo in sorted(mydict[param_name].keys(), reverse=True):
                #     val = mydict[param_name][geo]
                #     if geo in self.cty_idx:
                #         idxini = self.cty_idx[geo]['start']
                #         idxend = self.cty_idx[geo]['end']
                #         mymat[idxini:idxend, idx] = val
                #     else:
                #         mymat[self.geo_idx[geo], idx] = val
        tempmat = CalcVar(None, mymat, random_name=True)
        tempmat.sync_cache(self._cache, remote=True)
        self.def_mat[sector_name] = tempmat.name

    def compute_default_terrgroup(self, sector_name, param_name, terrgroup):
        '''
        '''
        if sector_name + '_' + param_name in self.def_vals:
            sub_def_vals = self.def_vals[sector_name + '_' + param_name]
        else:
            print('MISSING variable', sector_name + '_' + param_name)
            sub_def_vals = {}
            for geo in terrgroup['geocodes']:
                sub_def_vals[geo] = {'default': 0.000000001,
                                     'unit': 'base 100 en 2015',
                                     'operation_type': ['mean', ''],
                                     'type': 'percent_repartition',
                                     'min': 0.0, 'metadata': {'Population du territoire': [10832.0, 'sum']},
                                     'max': 100.0}
        list_defvals = []
        list_weights = []
        for geo in terrgroup['geocodes']:
            list_defvals.append(sub_def_vals[geo]['default'])
            if sub_def_vals[geo]['operation_type'][0] == 'mean':
                if sub_def_vals[geo]['operation_type'][1]:
                    list_weights.append(sub_def_vals[geo]['metadata'][sub_def_vals[geo]['operation_type'][1]][0])
                else:
                    list_weights.append(1)
        if sub_def_vals[geo]['operation_type'][0] == 'mean':
            return np.average(np.array(list_defvals), weights=np.array(list_weights))
        elif sub_def_vals[geo]['operation_type'][0] == 'sum':
            return np.array(list_defvals).sum()
        else:
            raise ValueError('Operation type is not mean nor sum : %s' % (sub_def_vals[geo]['operation_type'][0]))


class TerritoryGroups(Calculus):

    def _run(self, parameters, **kwargs):
        territorygroups = {}
        # self._cache.get_val('SimuParameters:%s' % (self._simu_id))
        param = self.get_variable(parameters)
        # Create updateVects : list of update in column1s of the matrix
        for section, hypotheses in param.items():
            for hypo in hypotheses:
                for territory in hypo['territory_groups']:
                    if __debug__:
                        logger.debug('Territory groups: %s', territory)
                    if territory['id'] != 'country':
                        try:
                            territorygroups[territory['id']]
                        except KeyError:
                            territorygroups[territory['id']] = territory['geocodes']
        return territorygroups


class ExtractSimulationMilestoneParameters(Calculus):

    def __init__(self, *args, **kwargs):
        '''
        gerer subgroup avec abs_val
        ajouter percent_repartition
        '''
        super().__init__(*args, **kwargs)
        # Always skip hash/cache because we return custom param matrix
        self._skip_cache = True
        self._skip_hash = True

    def _run(self, parameters, milestone_date, simu_defaults, pct_rep_w, **kwargs):
        '''
        For a given milestone compute the hypo ratios with respect to default values

        Parameters
        ----------
        parameters : dict
            dict of hypo for the associated milestone corresponding to the json sent by the saas

        milestone_date : datetime.datetime
            corresponding to the milestone

        simu_defaults : dict
            contains the computed default values, similar to 'Hypothesis:Default'

        Returns
        -------
        None
        '''
        self.set_types = self._cache.get_val('Hypothesis:Default:Absval')
        self.def_mat_ones = self._cache.get_val('Hypothesis:Default:Ones').copy()
        self.geo_idx = self._cache.get_val('geocodes_indexes')
        self.cty_idx = self._cache.get_val('counties_indexes')
        self.geocodes = self._cache.get_val('geocodes')
        self.tot_order = self._cache.get_val('Hypothesis:Default:Order')
        self.def_types = self._cache.get_val('Hypothesis:Default:Types')
        self.def_mat = simu_defaults.copy()
        self.pct_rep_w = pct_rep_w
        if __debug__:
            logger.info('Extracting Milestone Parameters :%s', milestone_date)

        # terr_groups = self.calculus('Simulation.TerritoryGroups', simu_specific=True)
        # simu_territory_groups = terr_groups(parameters=parameters)

        # defaults_ratios = self.def_mat_ones.copy()
        # defaults_vals = self.def_mat.copy()
        for hyp_name, hyp_ones in self.def_mat_ones.items():
            if __debug__:
                logger.info('Treating matrix %s', hyp_name)
            hyp_ones = self.default_ratios_builder(hyp_name, hyp_ones)
            self.def_mat_ones[hyp_name] = hyp_ones
            self.compute_ratios_from_params(hyp_name, parameters)
        return {'territory_groups': {}, 'param_matrix': self.def_mat_ones}

    def compute_ratios_from_params(self, hyp_name, parameters):
        ''' Computes the ratio of configured params to default values in order to perform the simulation

        Parameters
        ----------
        hyp_name : string
            hypothesis name, for example 'Demand_Tertiary_Consumption_Lighting'

        Returns
        -------
        None
        '''
        splitname = hyp_name.split('_')
        (var, cat) = ('_'.join(splitname[:-1]), splitname[-1])
        if var in parameters:
            params_var = parameters[var]
        else:
            return None
        hyp_reorder = self.reorder_params(hyp_name, params_var)
        if cat in hyp_reorder:
            hyp_cat = hyp_reorder[cat]
        else:
            return None
        def_vals_hyp = self.get_variable(CalcVar(None, self.def_mat[hyp_name], random_name=True))
        temp_value = self._update_cat_hyp(hyp_name, hyp_cat, def_vals_hyp)
        retMat = CalcVar(None, temp_value, random_name=True)
        coeffs_from_request = self.override_subcat_all(temp_value, self.tot_order[hyp_name], hyp_cat)
        retMat_ones = CalcVar(None, coeffs_from_request, random_name=True)
        if retMat._get_value(self._cache) is not None:
            self.def_mat_ones[hyp_name] = retMat_ones
            retMat_ones.sync_cache(self._cache)
        else:
            if __debug__:
                logger.error('Update Simu Param Matrix return none for hypothese %s', hyp_name)
            pass

    def override_subcat_all(self, coeffs, order, hyp_cat):
        '''
        Update all subcats in one go if one of the hyp is on subcat 'All'

        Parameters
        ----------
        coeffs :


        order : dict
            param_name and index of the corresponding np.ndarray for the current sector

        hyp_cat : dict
            reordered dict of hypothesis


        Returns
        -------
        dict
            nested dict with cat and subcat as keys instead of flat dict
        '''
        subcats = {key.split('_', 1)[0] for key in order.keys()}
        if 'All' in subcats:
            subcats_with_hypo = set(hyp_cat.keys())
            subcats_with_hypo.discard('All')
            subcats_without_all = subcats.copy()
            subcats_without_all.remove('All')
            variables = {key.split('_', 1)[1] for key in order.keys()}
            new_coeffs = coeffs.copy()
            for var in variables:
                for subcat in subcats_without_all:
                    new_coeffs[:, order['_'.join([subcat, var])]] = coeffs[:, order['_'.join(['All', var])]]
                for subcat in subcats_with_hypo:
                    new_coeffs[:, order['_'.join([subcat, var])]] = coeffs[:, order['_'.join([subcat, var])]]
            return new_coeffs
        else:
            return coeffs

    def reorder_params(self, hyp_name, params_var):
        ''' Reorders parameters from the json, in order to use category and subcats as keys of nested dict

        {'category': 'Consumption', 'subcategory': 'coach', 'territory_groups': [{'geocodes': ['FR99999']}]}
         becomes
         {'Consumption': {'coach': [{'geocodes': ['FR99999']}]}}

        Parameters
        ----------
        params_var : dict
            parameter values for one hypothesis

        Returns
        -------
        dict
            nested dict with cat and subcat as keys instead of flat dict
        '''
        ret = {}
        for hypo in params_var:
            cur = ret.get(hypo['category'], {})
            if __debug__:
                logger.debug('Cat : %s , hypo => %s', hypo['category'], cur)
            cur[hypo['subcategory']] = hypo['territory_groups']
            ret[hypo['category']] = cur
        hyp_sel = ret
        if __debug__:
            logger.debug('Construction of hypothese of %s : %s', hyp_name, ret)
        return ret

    def default_ratios_builder(self, hyp_name, hyp_ones):
        ''' Returns a CalcVar matrix of ones, allowing for abs_val to default at 0

        'Hypothesis:Default:Ones' returns a dict of hashed varnames for every hypothesis
        Every variable corresponding to such varname is a np.array at 1 with proper shape
        Here we wrap the varname in a CalcVar object
        We also take care of replacing default value to 0 for abs_val parameters

        Parameters
        ----------
        hyp_name : string
            hypothesis name, for example 'Demand_Tertiary_Consumption_Lighting'

        Returns
        -------
        CalcVar
            We go from a simple variable name to a CalcVar containing the values with
            inserted 0 in the case of abs_val
        '''
        if self.set_types[hyp_name]:
            hyp_ones = self.get_variable(CalcVar(None, hyp_ones, random_name=True))
            hyp_ones[:, self.set_types[hyp_name]] = 0
            hyp_ones = CalcVar(None, hyp_ones, random_name=True)
        else:
            hyp_ones = CalcVar(None, hyp_ones, random_name=True)
        return hyp_ones

    def _update_cat_hyp(self, hyp_name, hyp_cat, def_vals_hyp):
        '''
        Update default values with config values, first on territory groups then on subgroup

        Parameters
        ----------
        hyp_name : string
            hypothesis name, for example 'Demand_Tertiary_Consumption_Lighting'

        hyp_cat : dict
            containing reorganised parameter dict with subcat as keys

        def_vals_hyp : np.ndarray
            (36k,n) n being the number of params for sector_categ, containing default values

        Returns
        -------
        np.ndarray
            default values updated with hypothesis values
        '''
        # Create a new matrix from default one
        ret = def_vals_hyp.copy()
        if __debug__:
            logger.debug('hyp_name : %s | hypotheses : %s', hyp_name, hyp_cat)
        for subcat, territories in hyp_cat.items():
            # for subcat find geocodes (part of territory group or independant) for which said hyp has config values
            set_indices = self._territorygroup_update(hyp_name, subcat, territories, ret)
        for i in range(ret.shape[1]):
            if i not in set_indices:
                ret[:, i] = div0(ret[:, i], def_vals_hyp[:, i], replacement=1)
        return ret

    def _territorygroup_update(self, hyp_name, subcat, territories, ret):
        '''
        Update default values with config values, in the case of regular oldschool hypos

        Parameters
        ----------
        hyp_name : string
            hypothesis name, for example 'Demand_Tertiary_Consumption_Lighting'

        subcat : dict
            subcat name, like 'House'

        territories : dict
            containing the parameters for given hyp_name and subcat

        ret : np.ndarray
            hypos for hyp_name

        Returns
        -------
        None
        '''
        sterritories = {}
        for territory in territories:
            if __debug__:
                logger.debug('Territory : %s', territory)
            val_dict = {}
            list_geo = []
            if 'values' in territory:
                val_dict = territory['values']
                list_geo = territory['geocodes']
            subgroup = []
            if 'subgroup' in territory:
                subgroup = territory['subgroup']
            self._dispatch_hypos_togeo(hyp_name, subcat, list_geo, val_dict,
                                       sterritories, subgroup, self.def_types[hyp_name])
        if __debug__:
            logger.debug('Splitted hypotheses %s', sterritories)
        set_indices, index_abs_val = self._update_bygeo(sterritories, hyp_name, ret)
        index_abs_val = set(index_abs_val)
        self._update_abs_param(hyp_name, sterritories, index_abs_val, ret)
        return set_indices

    def _update_bygeo(self, sterritories, hyp_name, ret):
        '''
        Update default values in reverse geo order

        Parameters
        ----------
        hyp_name : string
            hypothesis name, for example 'Demand_Tertiary_Consumption_Lighting'

        sterritories : dict
            built to list geocode and value, i.e. unwrapping individual geocodes contained in a territory group

        ret : np.ndarray
            hypos for hyp_name

        Returns
        -------
        None
        '''
        index_abs_val = []
        set_indices = set()
        for geocode in sorted(sterritories.keys(), reverse=True):
            for param, val in sterritories[geocode].items():
                try:
                    if __debug__:
                        logger.debug('Hyp Name : %s, param : %s, value : %d', hyp_name, param, val)
                    index_name = self.tot_order[hyp_name][param]
                    if self.def_types[hyp_name][param] == 'abs_val':
                        index_abs_val.append((param, index_name))
                        set_indices.update({index_name})
                    else:
                        self._update_param_matrix(geocode, index_name, ret, val)
                except KeyError as e:
                    if __debug__:
                        logger.error('Error in update_cat discard %s : KeyError : %s, for hyp : %s',
                                     param, e, hyp_name)
                    raise
        return set_indices, index_abs_val

    def _update_abs_param(self, hyp_name, sterritories, index_abs_val, ret):
        '''
        Builds a dict applying abs hypo to the territories such that the sums of nested spatial units are ok

        Parameters
        ----------
        hyp_name : string
            hypothesis name, for example 'Demand_Tertiary_Consumption_Lighting'

        sterritories : dict
            contains the hypos for all the parameters of a given subcat and all territories concerned

        index_abs_val : list of tuples
            param name and its position in the np.ndarray

        ret : np.ndarray
            hypo array

        Returns
        -------
        None
        '''
        for param, index in index_abs_val:
            geo_dict = self._get_geo(param, sterritories)
            self._nested_update(hyp_name, geo_dict['FR99999'], ret, index, geocode='FR99999')

    def _nested_update(self, hyp_name, my_dict, ret, index, geocode=None):
        '''
        Recursive update of the hypo abs dict, so that the sums are ok

        Parameters
        ----------
        hyp_name : string
            hypothesis name, for example 'Demand_Tertiary_Consumption_Lighting'

        my_dict : dict
            contains the nested hypos

        index: int
            index of the current param in the np.ndarray

        ret : np.ndarray
            hypo array

        geocode : string
            a la 'FR99999'

        Returns
        -------
        None
        '''
        if len(my_dict) > 3:
            for key, val in my_dict.items():
                if isinstance(val, dict):
                    self._nested_update(hyp_name, val, ret, index, geocode=key)
        if my_dict['val'] is not None:
            self._get_indices_val(hyp_name, my_dict, geocode, ret, index)

    def _get_indices_val(self, hyp_name, my_dict, geocode, ret, index):
        '''
        Updates the containing spatial unit with subunit values, making sure to return the increment

        Parameters
        ----------
        hyp_name : string
            hypothesis name, for example 'Demand_Tertiary_Consumption_Lighting'

        my_dict : dict
            contains the nested hypos

        index: int
            index of the current param in the np.ndarray

        ret : np.ndarray
            hypo array

        geocode : string
            a la 'FR99999'

        Returns
        -------
        None
        '''
        defmat = self._cache.get_val('Hypothesis:Default')
        initdistrib = self.get_variable(CalcVar(None, defmat[hyp_name], random_name=True)).copy()
        if geocode in self.cty_idx:
            start = self.cty_idx[geocode]['start']
            end = self.cty_idx[geocode]['end']
            mask = np.ones(initdistrib[:, index].shape, dtype=bool)
            mask[: start] = 0
            mask[end:] = 0
            for geo in my_dict['list_geo']:
                if geo in self.cty_idx:
                    mask[self.cty_idx[geo]['start']: self.cty_idx[geo]['end']] = 0
                else:
                    mask[self.geo_idx[geo]] = 0
                    idx1 = self.geo_idx[geocode]
                    if geocode == 'FR99999':
                        ret[idx1, index] = my_dict['FR992' + geo[2:4]][geo]['val'] - initdistrib[idx1, index]
                    else:
                        ret[idx1, index] = my_dict[geo]['val'] - initdistrib[idx1, index]
            sumtot = initdistrib[mask, index].sum()
            if sumtot > 0:
                ret[mask, index] = initdistrib[mask, index] * ((my_dict['val'] - my_dict['sum']) / sumtot - 1)
            else:
                ret[mask, index] = (my_dict['val'] - my_dict['sum']) / mask.sum() - initdistrib[mask, index]
        else:
            idx1 = self.geo_idx[geocode]
            ret[idx1, index] = my_dict['val'] - initdistrib[idx1, index]

    def _get_geo(self, param, sterritories):
        '''
        Builds a nested dictionnary of the different geo scales and store hypo and their sum for abs_val

        Build nested dict and populate it :
        {'FR99999': {'val': None, 'sum': 0, 'list_geo': [],
                     county1 : {'val': None, 'sum': 0, 'list_geo': []}}}

        Parameters
        ----------
        param : string
            parameter name, for example 'All_power_wind_powerchangemw'

        sterritories : dict
            contains the hypos for all the parameters of a given subcat and all territories concerned

        Returns
        -------
        dict
            Nested to reflect geographical inclusion, and sums of hypos at the different scales
        '''
        geo_dict = {'FR99999': {'val': None, 'sum': 0, 'list_geo': []}}
        for county in self.cty_idx:
            if county != 'FR99999':
                geo_dict['FR99999'].update({county: {'val': None, 'sum': 0, 'list_geo': []}})
        # for param find all geocodes that have this param in sterritorries and sort
        ret_list = []
        for key, val in sterritories.items():
            if param in val:
                ret_list.append(key)
        ret_list.sort(reverse=True)
        # set values in geo_dict depending on the geographical scope of the geocode
        for geocode in ret_list:
            if geocode == 'FR99999':
                geo_dict[geocode]['val'] = sterritories[geocode][param]
            elif geocode in self.cty_idx:
                geo_dict['FR99999'][geocode]['val'] = sterritories[geocode][param]
                # if there is hypo for france and a county, keep track of the sum of the hypos and which county
                if geo_dict['FR99999']['val'] is not None:
                    geo_dict['FR99999']['sum'] += sterritories[geocode][param]
                    geo_dict['FR99999']['list_geo'].append(geocode)
            else:
                geo_dict['FR99999']['FR992' + geocode[2:4]][geocode] = {'val': sterritories[geocode][param]}
                if geo_dict['FR99999']['FR992' + geocode[2:4]]['val'] is None:
                    if geo_dict['FR99999']['val'] is not None:
                        geo_dict['FR99999']['sum'] += sterritories[geocode][param]
                        geo_dict['FR99999']['list_geo'].append(geocode)
                else:
                    geo_dict['FR99999']['FR992' + geocode[2:4]]['sum'] += sterritories[geocode][param]
                    geo_dict['FR99999']['FR992' + geocode[2:4]]['list_geo'].append(geocode)
        return geo_dict

    def _paramnames_vals_dict(self, hyp_name, subcat, val_dict, def_types, list_geo, subgroup):
        '''
        Reorder parameter dict in order to put whole param name as a key

        Parameters
        ----------
        subcat : string
            subcat name

        val_dict : dict
            contains the values associated to the territories

        ret : dict
            to be filled

        def_types: dict
            subdict of self.def_types for current cat

        mylen : int
            number of geocodes in territorygroup

        Returns
        -------
        np.ndarray
            dictionnary of hypo values
        '''
        raw_vals = self._param_geocode_val_dict(subcat, val_dict, subgroup)
        ret = {}
        list_pct = []
        for param_name, geodict in raw_vals.items():
            if def_types[param_name] == 'abs_val':
                self._group_abs_val(param_name, geodict, ret, list_geo)
            elif def_types[param_name] == 'percent_repartition':
                list_pct.append(param_name)
            else:
                self._group_default_attribution(param_name, geodict, ret, list_geo)
        list_grouped_pct = self.group_pct(list_pct, val_dict, subcat)
        setgrouped = set(['//'.join(sorted(subl)) for subl in list_grouped_pct])
        unique_grouped = []
        for el in list(setgrouped):
            temp = []
            for subname in el.split('//'):
                temp.append(subcat + '_' + subname)
            unique_grouped.append(temp)
        for group_param in unique_grouped:
            geodicts = [raw_vals[param_name] for param_name in group_param]
            self._group_percent_repartition(hyp_name, group_param, geodicts, ret, list_geo)
        return ret

    def group_pct(self, list_pct, val_dict, subcat):
        setfound = set()
        ret = []
        for param_name in list_pct:
            if param_name not in setfound:
                listkeys = []
                self.recursive_find_dict_path(param_name, val_dict, subcat, listkeys)
                ret.append([])
                for suffix in listkeys[-1]:
                    setfound.update('_'.join(listkeys[: -1] + [suffix]))
                    ret[-1].append('_'.join(listkeys[: -1] + [suffix]))
        return ret

    def recursive_find_dict_path(self, param_name, val_dict, tempname, listkeys):
        for key, val in val_dict.items():
            if tempname + '_' + key in param_name:
                if isinstance(val, dict):
                    listkeys.append(key)
                    self.recursive_find_dict_path(param_name, val, tempname + '_' + key, listkeys)
                else:
                    listkeys.append(list(val_dict.keys()))

    def _group_default_attribution(self, param_name, geodict, ret, list_geo):
        '''
        In the case of regular parameters, insert hypo value, override territory group by subgroup if necessary

        Parameter
        ----------
        param_name : string
            parameter name

        geodict : dict
            {geocode:val}

        ret : dict
            to be filled {geocode:{param:val}}

        list_geo: list
            list of geocodes in territory group

        Returns
        -------
        None
        '''
        for geo in list_geo:
            if geo in geodict:
                val = geodict[geo]
            elif 'group' in geodict:
                val = geodict['group']
            else:
                continue
            if geo in ret:
                ret[geo][param_name] = val
            else:
                ret[geo] = {param_name: val}

    def _group_abs_val(self, param_name, geodict, ret, list_geo):
        '''
        In the case of abs val, insert hypo value, override territory group by subgroup if necessary

        Keep track of weight of geocodes (if region weight is number of commune), start by subgroup
        After subgroup, apply remaining values with proper weight

        Parameter
        ----------
        param_name : string
            parameter name

        geodict : dict
            {geocode:val}

        ret : dict
            to be filled {geocode:{param:val}}

        list_geo: list
            list of geocodes in territory group

        Returns
        -------
        None

        Note
        ----
        Careful with territorygroup = {region, commune in said region}, then weights are a little bit off
        '''
        geo_w = {}
        tot_w = 0
        for geo in list_geo:
            if geo in self.cty_idx:
                geo_w[geo] = self.cty_idx[geo]['end'] - self.cty_idx[geo]['start']
            else:
                geo_w[geo] = 1
            tot_w += geo_w[geo]
        if 'group' in geodict:
            tot_val = geodict['group']
        for geo in geodict:
            if geo != 'group':
                if geo in ret:
                    ret[geo][param_name] = geodict[geo]
                else:
                    ret[geo] = {param_name: geodict[geo]}
                if 'group' in geodict:
                    tot_val -= geodict[geo]
                    tot_w -= geo_w[geo]
        if 'group' in geodict:
            for geo in list_geo:
                if geo not in geodict:
                    if geo not in ret:
                        ret[geo] = {param_name: tot_val * geo_w[geo] / tot_w}
                    else:
                        ret[geo][param_name] = tot_val * geo_w[geo] / tot_w

    def _group_percent_repartition(self, hyp_name, param_names, geodicts, ret, list_geo):
        '''
        In the case of percent repartition, insert hypo value, override territory group by subgroup if necessary

        Consider the constraints

        Parameter
        ----------
        param_name : string
            parameter name

        geodict : dict
            {geocode:val}

        ret : dict
            to be filled {geocode:{param:val}}

        list_geo: list
            list of geocodes in territory group

        Returns
        -------
        None
        '''
        setgeo = set()
        for geo in list_geo:
            if geo in self.cty_idx:
                setgeo.update(self.geocodes[self.cty_idx[geo]['start']: self.cty_idx[geo]['end']])
            else:
                setgeo.update([geo])
        for geo in geodicts[0]:
            if geo != 'group':
                if geo not in ret:
                    ret[geo] = {param_name: geodict[geo] for param_name, geodict in zip(param_names, geodicts)}
                else:
                    ret[geo].update({param_name: geodict[geo] for param_name, geodict in zip(param_names, geodicts)})
                if geo in self.cty_idx:
                    cty_geocodes = self.geocodes[self.cty_idx[geo]['start']: self.cty_idx[geo]['end']]
                    cty_geocodes = list(set(cty_geocodes) - set(list_geo))
                    listvals = [ret[geo][param_name] for param_name in param_names]
                    self.compute_pct_rep(param_names, cty_geocodes, listvals, ret)
                    setgeo = setgeo - set(cty_geocodes)
                else:
                    setgeo - set([geo])
        if 'group' in geodicts[0]:
            listvals = [geodict['group'] for geodict in geodicts]
            self.compute_pct_rep(hyp_name, param_names, setgeo, listvals, ret)

    def compute_pct_rep(self, hyp_name, param_names, list_geo, listvals, ret):
        param_idxs = [self.tot_order[hyp_name][param_name] for param_name in param_names]
        geo_idxs = [self.geo_idx[geo] for geo in list_geo]
        tempcalc = CalcVar(None, self.def_mat[hyp_name], random_name=True)
        raw_pts = self.get_variable(tempcalc)[geo_idxs, :][:, param_idxs].copy()
        raw_w = np.expand_dims(self.pct_rep_w[hyp_name][param_names[0]][geo_idxs].copy(), axis=1)
        abs_pts = raw_pts * raw_w
        tot_pt = abs_pts.sum(axis=0)
        tot_pt_new = np.array(listvals) * raw_w.sum()
        if not all(tot_pt == tot_pt_new):
            delta_vect = tot_pt_new - tot_pt
            dists = self.delta_to_dists(abs_pts, delta_vect)
            pdeltas = self.point_deltas(dists, delta_vect)
            new_pts = abs_pts + pdeltas
            new_pts_renormed = div0(new_pts, raw_w)
        else:
            new_pts_renormed = raw_pts
        for idxx, geo in enumerate(list_geo):
            for idxy, param_name in enumerate(param_names):
                if geo in ret:
                    ret[geo][param_name] = new_pts_renormed[idxx, idxy]
                else:
                    ret[geo] = {param_name: new_pts_renormed[idxx, idxy]}

    def delta_to_dists(self, abs_pts, delta_vect):
        dists = []
        for onep in abs_pts:
            coeffs = []
            totsum = onep.sum()
            for idx, val in enumerate(onep):
                if delta_vect[idx] == 0:
                    coeffs.append(1e10)
                    coeffs.append(1e10)
                else:
                    coeffs.append(-val / delta_vect[idx])
                    coeffs.append((totsum - val) / delta_vect[idx])
            coeffs = np.array(coeffs)
            coeffs[np.where(coeffs < 0)] = coeffs.max()
            dists.append(coeffs.min())
        return np.array(dists)

    def dist_to_ref(self, idxref, abs_pts, delta_vect):
        dists = []
        for idx, point in enumerate(abs_pts):
            dists.append(np.abs(-point[idxref] / delta_vect[idxref]))
        return np.array(dists)

    def point_deltas(self, dists, delta_vect):
        return np.expand_dims(dists, axis=1) * np.expand_dims(delta_vect, axis=0) / dists.sum()

    def _param_geocode_val_dict(self, subcat, group_vals, subgroup):
        '''
        From values for the territory group and subgroup build a dict containing param_name : geocode : value

        Parameters
        ----------
        subcat : string
            subcat name

        group_vals : dict
            values for the territory group

        subgroup : dict
            geocodes as keys
            associated config values when user configures an independent geocode from a territorygroup

        Returns
        -------
        dict
            Flattened dictionnary of hypos for the whole territory group and subgroup
        '''
        if group_vals:
            temp1 = {'group': group_vals}
        else:
            temp1 = {}
        for geo in subgroup:
            temp1[geo] = subgroup[geo]['values']
        temp2 = {}
        for geo in temp1:
            initdict = {}
            self._flatten_name_value(subcat, temp1[geo], initdict)
            temp2[geo] = initdict
        ret = {}
        for geo, paramdict in temp2.items():
            for param_name, val in paramdict.items():
                if param_name in ret:
                    ret[param_name][geo] = val
                else:
                    ret[param_name] = {geo: val}
        return ret

    def _flatten_name_value(self, varname, mydict, store):
        '''
        Recursively flatten nested param names to a single '_'.join string and the associated value

        Parameters
        ----------
        varname : string
            '_' joined keys of the previous calls of this nested function

        mydict : dict
            current subdict of global hyp dict

        store : dict
            initialised as empty, and filled only with concatenated string as a single level dict of param_name : val

        Returns
        -------
        dict
            param_names : vals
        '''
        for key, val in mydict.items():
            newname = varname + '_' + key
            if isinstance(val, dict):
                self._flatten_name_value(newname, val, store)
            elif isinstance(val, list):
                raise ValueError('Hypo subdict has a list as value %s for param %s' % (val, newname))
            else:
                store[newname] = val

    def _dispatch_hypos_togeo(self, hyp_name, subcat, list_geo, val_dict, ret, subgroup, def_types):
        '''
        To every geocode associate a dict containing the param names and the values

        Parameters
        ----------
        subcat : string
            subcat name

        val_dict : dict
            contains the values associated to the territories

        ret : dict
            geocodes and the hypo vals for the current cat parameters

        def_types: dict
            subdict of self.def_types for current cat

        list_geo : list
            list of geocodes

        subgroup : dict
            geocodes as keys
            associated config values when user configures an independent geocode from a territorygroup

        Returns
        -------
        None
        '''
        value = self._paramnames_vals_dict(hyp_name, subcat, val_dict, def_types, list_geo, subgroup)
        for geocode in value:
            if geocode in ret:
                if __debug__:
                    logger.warning('Found geocode %s in multiple hypotheses : %s and %s',
                                   geocode, ret[geocode], val_dict)
                pass
            else:
                ret[geocode] = value[geocode]

    def _update_param_matrix(self, geocode, index, ret, val):
        '''
        Update default value for a given geocode and param index

        Parameters
        ----------
        geocode : string
            geocode name, can be a county

        index : int
            index of column corresponding to the parameter to be udpated

        ret : np.ndarray
            shape (Ngeo, Nparams) corresponding to the default values

        val : float
            value with which ret is to be updated in col index and line corresponding to geocode

        Returns
        -------
        None
            updates the ret array in place
        '''
        if geocode < 'FR99000':
            try:
                geo_ind = self.geo_idx[geocode]
                if __debug__:
                    logger.debug('Updating matrix element [%d,%d] with %d', geo_ind, index, val)
                ret[geo_ind, index] = val
            except KeyError as e:
                if __debug__:
                    logger.error('Unknown geocode %s : %s', geocode, e)
                raise
        else:
            try:
                county = self.cty_idx[geocode]
                if __debug__:
                    logger.debug('Updating matrix elements [%d:%d,%d] with %d',
                                 county['start'], county['end'], index, val)
                ret[county['start']: county['end'], index] = np.repeat([[val]], county['end'] - county['start'])
            except KeyError as e:
                if __debug__:
                    logger.error('Unknown county %s : %s', geocode, e)
                raise
