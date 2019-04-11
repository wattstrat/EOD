import re

import csv
import numpy as np

import Config.config as config
import Config.variables as variables

from Calculus.Initialisation.Initialisation import Initialisation
from Calculus.calculus import Calculus
from Calculus.CalcVar import CalcVar
from babel.dot._auto_parameters_definition import auto_parameters_definition


if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class DefMatrixBuilderConstants(Calculus):

    def _run(self, *args, **kwargs):
        # Geocode should be initialised
        # to create matrices with the same number of lines as geocodes number
        geocode_number = len(self._cache.get_val('geocodes'))
        self.N_geo = geocode_number

        matrix = self._create_matdict(geocode_number)
        matrix_ones = {}
        if __debug__:
            logger.debug('Returned matrix : %s', matrix)
        ordermatrix = {}
        named_matrix = {}
        for section, vects in matrix.items():
            varkey, varvects = zip(*vects.items())
            varmat = np.stack(varvects, axis=-1)
            var_namedmat = np.core.records.fromarrays(varvects, names=','.join(varkey))
            varorder = {x: varkey.index(x) for x in varkey}
            ordermatrix[section] = varorder
            varcalc = CalcVar(None, varmat, random_name=True)
            var_namedcalc = CalcVar(None, var_namedmat, random_name=True)
            varones = CalcVar(None, np.ones(varmat.shape), random_name=True)
            matrix[section] = varcalc.name
            named_matrix[section] = var_namedcalc.name
            matrix_ones[section] = varones.name
            # Synchronise the caches
            varcalc.sync_cache(self._cache, remote=True)
            var_namedcalc.sync_cache(self._cache, remote=True)
            varones.sync_cache(self._cache, remote=True)

        self._cache.set_val('Hypothesis:Default:Ones', matrix_ones)
        self._cache.set_val('Hypothesis:Default', matrix)
        self._cache.set_val('Hypothesis:Default:Named', named_matrix)
        self._cache.set_val('Hypothesis:Default:Order', ordermatrix)
        self._cache.set_val('Hypothesis:Default:Absval', self._abs_val_sections(ordermatrix))
        return None

    def _create_matdict(self, N_geo):
        self.count = 0
        previous_line = [0, 0, 0, 0]
        matrixdict = {}
        matrix_types = {}
        for key, val in auto_parameters_definition.items():
            for category in val['categories']:
                section = '_'.join([key, category['name']])
                if section not in matrixdict:
                    matrixdict[section] = {}
                    matrix_types[section] = {}
                for subcat in category['subcategories']:
                    if 'hypotheses' in subcat:
                        self._hypo_block_update(section, matrixdict, matrix_types, subcat, subcat['name'])
                    else:
                        self._hypo_block_update(section, matrixdict, matrix_types, category, subcat['name'])
        self._cache.set_val('Hypothesis:Default:Types', matrix_types)
        return matrixdict

    def _abs_val_sections(self, ordermatrix):
        set_abs_val = {}
        matrix_types = self._cache.get_val('Hypothesis:Default:Types')
        for sec, myvariables in matrix_types.items():
            set_abs_val[sec] = []
            for myvariable, vartype in myvariables.items():
                if vartype == 'abs_val':
                    set_abs_val[sec].append(ordermatrix[sec][myvariable])
        return set_abs_val

    def _hypo_block_update(self, section, mat_dict, mat_types, block, subname):
        for hypo in block['hypotheses']:
            if 'parameter' in hypo:
                self._build_hypo_param(section, mat_dict, mat_types, block, subname, hypo['parameter'])
            elif 'parametersGroup' in hypo:
                for subhypo in hypo['parametersGroup']:
                    self._build_hypo_param(section, mat_dict, mat_types, block, subname, subhypo)

    def _build_hypo_param(self, section, mat_dict, mat_types, block, subname, hyp):
        if 'pack' in hyp:
            for pack in hyp['pack']:
                self._default_val(section, mat_dict, mat_types, block, subname, hyp, pack)
        else:
            pack = {'name': '', 'default': hyp['default']}
            self._default_val(section, mat_dict, mat_types, block, subname, hyp, pack)

    def _default_val(self, section, mat_dict, mat_types, block, subname, hyp, pack):
        self.count += 1
        varname = '_'.join([subname, hyp['name'], pack['name']])
        if varname[-1] == '_':
            varname = varname[:-1]
        mat_types[section][varname] = hyp['type']
        if hyp['type'] == 'abs_val':
            mat_dict[section][varname] = self._default_abs_val(section, varname)
        else:
            if pack['default'] == 0:
                if __debug__:
                    logger.warning('Default value for section %s and variable %s is 0, '
                                   'which will cause problems when dividing', section, varname)
            mat_dict[section][varname] = np.repeat([[pack['default']]], self.N_geo).astype('float')

    def _default_abs_val(self, section, varname):
        runkwargs = {'category': section.split('_')[-1], 'varname': varname}
        default_val = self._cache.get_val(section + ':' + varname, run_kwargs=runkwargs)
        return default_val
