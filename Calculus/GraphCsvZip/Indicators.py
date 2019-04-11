import numpy as np
import pickle
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import math
import csv

from Calculus.GraphCsvZip.Numpy import rollingMax, rollingMin, rollingMean


#get_ipython().run_line_magic('matplotlib', 'inline')
def eng_string(x, format='%s', si=False, onlySI=False):
    '''
    Returns float/int value <x> formatted in a simplified engineering format -
    using an exponent that is a multiple of 3.

    format: printf-style string used to format the value before the exponent.

    si: if true, use SI suffix for exponent, e.g. k instead of e3, n instead of
    e-9 etc.

    E.g. with format='%.2f':
        1.23e-08 => 12.30e-9
             123 => 123.00
          1230.0 => 1.23e3
      -1230000.0 => -1.23e6

    and with si=True:
          1230.0 => 1.23k
      -1230000.0 => -1.23M
    '''
    sign = ''
    if x < 0:
        x = -x
        sign = '-'
    if x == 0:
        x = 1
    exp = int(math.floor(math.log10(x)))
    exp3 = exp - (exp % 3)
    x3 = x / (10 ** exp3)
    if si and exp3 >= -24 and exp3 <= 24 and exp3 != 0:
        exp3_text = 'yzafpnum kMGTPEZY'[int((exp3 - (-24)) / 3)]
    elif exp3 == 0:
        exp3_text = ''
    else:
        exp3_text = 'e%s' % exp3
    if onlySI:
        return exp3_text, 10**exp3
    return ('%s' + format + '%s') % (sign, x3, exp3_text)


class Graph3YearsMixIn(object):

    def computeGraphFilename(self, ind, scenar, year):
        return '%s.png' % (scenar)

    def clearCurrentGraph(self, indVar, scenar, year):
        return indVar is not None and scenar is not None and year is None

    def saveCurrentGraph(self, indVar, scenar, year):
        return indVar is not None and scenar is not None and year is None


class BasicIndicateur(object):
    variable_label = {
        'total_demand': 'Demande totale',
        'net_demand': 'Demande nette du pilotage de la demande',
        'demand_to_match': 'Demande adressée aux moyens pilotables hors hydro',
        'wind_onshore': 'Éolien terrestre',
        'wind_offshore': 'Éolien offshore',
        'pv': 'Photovoltaïque',
        'marine_hydro': 'Hydroliennes',
        'hydrolake': 'Hydraulique Lacs',
        'hydrostep': 'Hydraulique STEP',
        'hydro_run': "Hydraulique fil de l'eau",
        'default_sure': 'Défaut (positif) et surprod (négatif)',
        'tot_interco': 'Interconnexions',
        'Nucleaire': 'Nucléaire'
    }

    def __init__(self, *args, variables, scenarios, years,  datas, name=None, graphOptions={}, options={}, **kwargs):
        super().__init__()
        self.graphOptions = {}
        self.options = {}
        self.name = None
        self.siT = None
        self.puiss = None
        self.forceSiT = None
        self.forcePuiss = None

        self.variables = variables
        self.scenarios = scenarios
        self.years = years

        self.datas = datas

        if name is not None:
            self.name = name
        elif self.name is None:
            self.name = self.__class__.__name__

        self.filenameCSV = None
        self.hFileCSV = None
        self.writerCSV = None

        self.options.update(options)

        self.graphOptions.update(graphOptions)

    def init(self, writerCSV=None, filenameCSV=None, hFileCSV=None):
        self.computeVarNames()
        if self.forceSiT is not None:
            self.siT = self.forceSiT
            self.puiss = self.forcePuiss

        if not self.options.get('noCSV', False):
            self.filenameCSV = filenameCSV
            # OK, on écrit dans un CSV
            if writerCSV is None:
                if self.filenameCSV is None:
                    self.filenameCSV = "export.csv"
                self.hFileCSV = open(self.filenameCSV, 'w+')
                self.writerCSV = csv.writer(self.hFileCSV)
                self.writerCSV.writerow(self.headerCSV())
            else:
                self.writerCSV = writerCSV
                self.hFileCSV = hFileCSV

    def computeVarNames(self):
        self.varNames = []
        self.varNamesCSV = []
        for ind, var in enumerate(self.variables):
            if type(var) not in [list, str]:
                print("Error for config %s in variables pos %d" % (self.name, ind))
                continue

            if type(var) is list:
                if len(var) == 0:
                    return
                varName = ','.join([self.variable_label.get(v, v) for v in var])
                self.varNames.append(varName)
                self.varNamesCSV.append("%s sur %s" % (self.name, varName))
            elif type(var) is str:
                varName = self.variable_label.get(var, var)
                self.varNames.append(varName)
                self.varNamesCSV.append("%s sur %s" % (self.name, varName))

    def formatDataCSV(self, val):
        return "%s" % val

    def closeCSV(self):
        if self.options.get('closeCSV', True) and self.hFileCSV is not None:
            self.hFileCSV.close()
            self.hFileCSV = None
            self.writerCSV = None

    def compute(self):
        if self.options.get('Y', "variables") == "variables":
            self.computeVarByScenarYear()
        else:
            self.computeScenarYearByVar()

        self.closeCSV()
        return {
            'writerCSV': self.writerCSV,
            'hFileCSV': self.hFileCSV
        }

    def computeVars(self, var, courbes):
        if type(var) is list:
            if len(var) == 0:
                return {}
            if type(var[0]) is list:
                return [{k: courbes[k] for k in v} for v in var]
            else:
                return {k: courbes[k] for k in var}
        elif type(var) is str:
            return courbes[var]

    def getRowHeader(self, index):
        return self.varNamesCSV[index]

    def computeVarByScenarYear(self):
        self.beforeCSV('var', None, None, None)
        for ind, var in enumerate(self.variables):
            print("   - var ind %d (%s)" % (ind, self.varNames[ind] if ind < len(self.varNames) else ''))
            vals = [self.getRowHeader(ind)]
            self.beforeCSV('scenar', ind, None, None)
            for scenar in self.scenarios:
                if scenar not in self.datas:
                    print('    === ERROR: scenar %s missing from data' % scenar)
                    continue
                annees = self.datas[scenar]
                self.beforeCSV('annee', var, scenar, None)
                for annee in self.years:
                    if annee not in annees:
                        print('    === ERROR: year %s missing from data scenar %s' % (annee, scenar))
                        continue

                    courbes = annees[annee]
                    print("     * Scenarion %s / Année %s\b" % (scenar, annee))
                    self.computeCourbesScenarYear(courbes, vals, ind, var, scenar, annee)
                self.afterCSV('annee', var, scenar, None)
                if self.saveCurrentGraph(ind, scenar, None):
                    graphFilename = self.computeGraphFilename(ind, scenar, annee)
                    self.saveGraph(graphFilename, **self.graphOptions)
                if self.clearCurrentGraph(ind, scenar, None):
                    self.clearGraph()
            if self.saveCurrentGraph(ind, None, None):
                graphFilename = self.computeGraphFilename(ind, scenar, annee)
                self.saveGraph(graphFilename, **self.graphOptions)
            if self.clearCurrentGraph(ind, None, None):
                self.clearGraph()
            if self.saveCurrentCSVRow():
                self.saveCSV(vals)
            self.afterCSV('scenar', var, None, None)
        self.afterCSV('var', None, None, None)
        if self.saveCurrentGraph(None, None, None):
            graphFilename = self.computeGraphFilename(ind, scenar, annee)
            self.saveGraph(graphFilename, **self.graphOptions)
        if self.clearCurrentGraph(None, None, None):
            self.clearGraph()

    def clearGraph(self):
        plt.clf()
        self.siT = None
        self.puiss = None
        if self.forceSiT is not None:
            self.siT = self.forceSiT
            self.puiss = self.forcePuiss

    def computeGraphFilename(self, ind, scenar, year):
        return '%s - %d  - %s sur %s.png' % (scenar, year, self.name, self.varNames[ind])

    def clearCurrentGraph(self, indVar, scenar, year):
        if self.options.get('noGraph', False):
            return False

        if self.options.get('clearGraph', True):
            return True

        if not self.options.get('clearGraphBetweenScenar', True):
            return year is None
        return True

    def saveCurrentGraph(self, indVar, scenar, year):
        if self.options.get('noGraph', False):
            return False
        if not self.options.get('clearGraphBetweenYear', True):
            return indVar is not None and scenar is not None and year is None
        # save only in most inner loop
        return indVar is not None and scenar is not None and year is not None

    def saveCurrentCSVRow(self):
        return not self.options.get('noCSV', False)

    def formatScenarioAnneeCSV(self, scenar, annee):
        return "Scenarion %s / Année %s" % (scenar, annee)

    def computeScenarYearByVar(self):
        self.beforeCSV('scenar', None, None, None)
        for scenar in self.scenarios:
            if scenar not in self.datas:
                print('    === ERROR: scenar %s missing from data' % scenar)
                continue
            annees = self.datas[scenar]
            self.beforeCSV('annee', None, scenar, None)
            for annee in self.years:
                if annee not in annees:
                    print('    === ERROR: year %s missing from data scenar %s' % (annee, scenar))
                    continue
                print("   * Scenarion %s / Année %s\b" % (scenar, annee))
                courbes = annees[annee]
                vals = [self.formatScenarioAnneeCSV(scenar, annee)]
                self.beforeCSV('var', None, scenar, annee)
                for ind, var in enumerate(self.variables):
                    print("   - var ind %d (%s)" % (ind, self.varNames[ind] if ind < len(self.varNames) else ''))
                    self.computeCourbesScenarYear(courbes, vals, ind, var, scenar, annee)
                self.afterCSV('var', None, scenar, annee)
                if self.saveCurrentGraph(None, scenar, annee):
                    graphFilename = self.computeGraphFilename(ind, scenar, annee)
                    self.saveGraph(graphFilename, **self.graphOptions)
                if self.clearCurrentGraph(None, scenar, annee):
                    self.clearGraph()

                if self.saveCurrentCSVRow():
                    self.saveCSV(vals)
            self.afterCSV('annee', None, scenar, None)
            if self.saveCurrentGraph(None, scenar, None):
                graphFilename = self.computeGraphFilename(ind, scenar, annee)
                self.saveGraph(graphFilename, **self.graphOptions)
            if self.clearCurrentGraph(None, scenar, None):
                self.clearGraph()
        self.afterCSV('scenar', None, None, None)
        if self.saveCurrentGraph(None, None, None):
            graphFilename = self.computeGraphFilename(ind, scenar, annee)
            self.saveGraph(graphFilename, **self.graphOptions)
        if self.clearCurrentGraph(None, None, None):
            self.clearGraph()

    def computeCourbesScenarYear(self, courbes, vals, ind, var, scenar, annee):
        var_a = self.computeVars(var, courbes)

        vals.append(self.formatDataCSV(self.computeFunCourbesScenarYear(var_a, ind, scenar, annee, courbes)))
        if self.saveCurrentGraph(ind, scenar, annee):
            graphFilename = self.computeGraphFilename(ind, scenar, annee)
            self.saveGraph(graphFilename, **self.graphOptions)
        if self.clearCurrentGraph(ind, scenar, annee):
            self.clearGraph()

    def computeFunCourbesScenarYear(self, courbes, indVar, scenario, annee, allCourbes):
        raise NotImplemented("compute not implemented")

    @classmethod
    def test(cls):
        import pickle
        datas = pickle.load(file=open("notebook/data.json.bin", 'rb'))
        kwargs = cls.test_kwargs(datas)
        T = cls(**kwargs)
        T.initWriter(kwargs.get('writerCSV'), kwargs.get('filenameCSV'))
        T.compute()

    def saveGraph(self, filename, size=(12, 6), dpi=100, base_path='Graphs/', **kwargs):
        fig = plt.gcf()
        fig.set_size_inches(*size)
        fig.savefig(base_path + filename, dpi=dpi)

    def saveCSV(self, vals):
        if self.writerCSV is not None:
            self.beforeLineCSV()
            self.writerCSV.writerow(self.formatLineCSV(vals))
            self.afterLineCSV()

    def getHeaderLabels(self):
        return ("Scénario - Années", "Variables")

    def headerCSV(self):
        (xLabel, yLabel) = self.getHeaderLabels()
        if self.options.get('Y', "variables") == "variables":
            headers = ["%s / %s" % (yLabel, xLabel)] + ["Scénario %s / Année %s" % (scenar, annee)
                                                        for scenar in self.scenarios for annee in self.years]
        else:
            headers = ["%s / %s" % (xLabel, yLabel)] + self.varNamesCSV

        return headers

    def formatLineCSV(self, vals):
        return vals

    def beforeLineCSV(self):
        pass

    def afterLineCSV(self):
        pass

    def beforeCSV(self, typeEvent='', var=None, scenar=None, year=None):
        pass

    def afterCSV(self, typeEvent='', var=None, scenar=None, year=None):
        pass


class Pmax(BasicIndicateur):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        options = {
            'Y': 'variables'
        }
        options.update(self.options)
        self.options = options
        self.name = "Puissance maximal (en GW)"

    def computeFunCourbesScenarYear(self, courbes, indVar, scenario, annee, allCourbes):
        # Courbes doit être une seule courbe
        nPmax = float(np.max(courbes))
        if not self.options.get('noGraph', False):
            #plt.legend(loc='upper right')
            plt.title('%s - histogramme puissance - Pmax: %sW' % (scenario, eng_string(nPmax, format="%0.2f", si=True)))
            if self.siT is None:
                siT, puiss = eng_string(nPmax, si=True, onlySI=True)
                self.siT = siT
                self.puiss = puiss
            else:
                siT = self.siT
                puiss = self.puiss
            courbe_norm = courbes / puiss
            #axes = plt.gca()
            #axes.set_ylim([0, 100])
            plt.xlabel('Puissance en %sW' % (siT))
            plt.ylabel("Nombre d'heures")
            plt.hist(courbe_norm, bins=100)

        # en gigawatt
        return nPmax / 10**9

    @staticmethod
    def test_kwargs(datas):
        courbes = datas['perspective_2017']
        d = {'SCENAR1': {2015: courbes}}
        scenarios = ['SCENAR1']
        years = [2015]
        variables = ['total_demand']
        return {
            'variables': variables,
            'scenarios': scenarios,
            'years': years,
            'datas': d,
            'name': "P-MAX",
            'filenameCSV': "test/Pmax.csv",
            'graphOptions': {'base_path': "test/"},
        }


class GraphVariables(BasicIndicateur):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.name = "Courbe de la variable"
        graphOptions = {
            'title': '{scenario}/{annee} - {varname} en {si}W',
            'label': None,
        }
        if 'window'in kwargs:
            self.window = slice(*kwargs.get('window'))
        else:
            self.window = slice(None)
        graphOptions.update(self.graphOptions)
        self.graphOptions = graphOptions
        self.noCSV = True

    def computeFunCourbesScenarYear(self, courbes, indVar, scenario, annee, allCourbes):
        if not self.options.get('noGraph', False):
            if type(courbes) is dict:
                courbes = np.sum(list(courbes.values()), axis=0)
            maxCourbe = np.max(courbes)
            minCourbe = np.min(courbes)
            if self.siT is None:
                siT, puiss = eng_string(max(maxCourbe, -minCourbe), si=True, onlySI=True)
                self.siT = siT
                self.puiss = puiss
            else:
                siT = self.siT
                puiss = self.puiss
            plt.title(self.graphOptions['title'].format(scenario=scenario, annee=annee,
                                                        varname=self.varNames[indVar], si=siT, window=self.window))

            courbe_norm = courbes / puiss
            plt.ylabel('Variable en %sW' % (siT))
            if self.window.start is None or self.window.start == 0:
                plt.xlabel('Index horaire - 0 correspond au 1er janvier à 00h00')
            else:
                plt.xlabel('Index horaire - 0 correspond à la %d heures à partir du 1er janvier à 00h00' %
                           self.window.start)
            if self.graphOptions['label'] is None:
                lbl = '%s en %sW' % (self.varNames[indVar], siT)
            else:
                lbl = self.graphOptions['label'].format(scenario=scenario, annee=annee, varname=self.varNames[
                                                        indVar], si=siT, window=self.window, minpositif='%.2f%s' % (-minCourbe / puiss, siT), maxpositif='%.2f%s' % (maxCourbe / puiss, siT))
            if 'additionalText' in self.graphOptions:
                plt.text(*self.graphOptions['additionalText']['args'], **self.graphOptions['additionalText']['kwargs'])
            plt.plot(courbe_norm[self.window], label=lbl)
            plt.legend(loc='best')

        return None

    def computeGraphFilename(self, ind, scenar, year):
        return '%s - %d  - %s .png' % (scenar, year, self.varNames[ind])

    @staticmethod
    def test_kwargs(datas):
        courbes = datas['perspective_2017']
        d = {'SCENAR1': {2015: courbes}}
        scenarios = ['SCENAR1']
        years = [2015]
        variables = [list(courbes.keys())]
        return {
            'variables': variables,
            'scenarios': scenarios,
            'years': years,
            'datas': d,
            'noCSV': True,
            'graphOptions': {'base_path': "test/"},
        }


class GraphVariablesGraph3Years(Graph3YearsMixIn, GraphVariables):
    pass


class PminEnR(BasicIndicateur):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.name = "Puissance minimal des EnR"
        graphOptions = {
            'width': 7 * 24,
            'title': '{scenario}/{annee} - EnR - Pmin: {pmin}W',
            'label': None,
            'label_sum': None,
            'width_label': '7 jours',
            'with_sum': False,
        }
        graphOptions.update(self.graphOptions)
        self.graphOptions = graphOptions

    def computeFunCourbesScenarYear(self, courbes, indVar, scenario, annee, allCourbes):
        EnR = np.sum(list(courbes.values()), axis=0)
        nPmin = float(np.min(EnR))
        if not self.options.get('noGraph', False):
            plt.title(self.graphOptions['title'].format(scenario=scenario,
                                                        annee=annee, pmin=eng_string(nPmin, format="%0.2f", si=True)))
            if self.siT is None:
                siT, puiss = eng_string(nPmin, si=True, onlySI=True)
                self.siT = siT
                self.puiss = puiss
            else:
                siT = self.siT
                puiss = self.puiss
            courbe_norm = EnR / puiss
            #axes = plt.gca()
            #axes.set_ylim([0, 100])
            plt.ylabel('Puissance minimal en %sW' % (siT))
            plt.xlabel('Index horaire - 0 correspond au 1er janvier à 00h00')
            if self.graphOptions['label'] is None:
                lbl = 'Minimum puissance glissant sur ' + self.graphOptions['width_label']
            else:
                lbl = self.graphOptions['label'].format(
                    scenario=scenario, annee=annee, pmin=eng_string(nPmin, format="%0.2f", si=True))
            plt.plot(rollingMin(courbe_norm, self.graphOptions['width']), label=lbl)
            if self.graphOptions['with_sum']:
                if self.graphOptions['label_sum'] is None:
                    lbl = 'Minimum puissance glissant sur ' + self.graphOptions['width_label']
                else:
                    lbl = self.graphOptions['label_sum'].format(
                        scenario=scenario, annee=annee, pmin=eng_string(nPmin, format="%0.2f", si=True))
                plt.plot(courbe_norm, label=lbl)
            plt.legend(loc='best')

        return nPmin

    def getRowHeader(self, index):
        # Il ne devrait y avoir qu'une seule "variables"
        return "Pmin sur les EnR"

    def computeGraphFilename(self, ind, scenar, year):
        return '%s - %d  - Pmin sur EnR.png' % (scenar, year)

    @staticmethod
    def test_kwargs(datas):
        courbes = datas['perspective_2017']
        d = {'SCENAR1': {2015: courbes}}
        scenarios = ['SCENAR1']
        years = [2015]
        variables = [list(courbes.keys())]
        return {
            'variables': variables,
            'scenarios': scenarios,
            'years': years,
            'datas': d,
            'name': "P-MIN",
            'filenameCSV': "test/Pmin.csv",
            'graphOptions': {'base_path': "test/"},
        }


class PminEnRGraph3Years(PminEnR):

    def computeGraphFilename(self, ind, scenar, year):
        return '%s.png' % (scenar)

    def clearCurrentGraph(self, indVar, scenar, year):
        return indVar is not None and scenar is not None and year is None

    def saveCurrentGraph(self, indVar, scenar, year):
        return indVar is not None and scenar is not None and year is None


class StatsDefault(BasicIndicateur):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # construct internal default memory
        self.defaults = {k: {} for k in self.scenarios}
        # Not common variables
        self.name = "Statistique Defaut"
        graphOptions = {
            'title': '{scenario}/{annee} - Defaut - Max ({typeD}): {puiss}W/{hour}h',
            'label': None,
        }
        graphOptions.update(self.graphOptions)
        self.graphOptions = graphOptions

        self.variables = ['default_sure'] * 4

    def getRowHeader(self, index):
        LABEL = ['Type du défaut maximum',
                 "Nombre d'heures consécutives du plus long défaut de l'année",
                 "Énergie totale du plus long défaut de l'année (GWh)",
                 "Énergie totale des défauts sur l'année (GWh)"]

        return LABEL[index]

    @staticmethod
    def extractDefault(courbe):
        last_P_ind = None
        last_N_ind = None
        all_default = []
        for ind, val in enumerate(courbe):
            if val >= 0 and last_N_ind is not None:
                hours = (ind - last_N_ind)
                all_default.append((-1, hours, -np.sum(courbe[last_N_ind:ind]), last_N_ind))
                last_N_ind = None
            if val <= 0 and last_P_ind is not None:
                hours = (ind - last_P_ind)
                all_default.append((1, hours, np.sum(courbe[last_P_ind:ind]), last_P_ind))
                last_P_ind = None
            if val > 0 and last_P_ind is None:
                last_P_ind = ind
            if val < 0 and last_N_ind is None:
                last_N_ind = ind
        ind = len(courbe)
        if last_P_ind is not None:
            hours = (ind - last_P_ind)
            all_default.append((1, hours, np.sum(courbe[last_P_ind:ind]), last_P_ind))
        if last_N_ind is not None:
            hours = (ind - last_N_ind)
            all_default.append((-1, hours, -np.sum(courbe[last_N_ind:ind]), last_N_ind))
        return all_default

    def computeGraphFilename(self, ind, scenar, year):
        return '%s - %d  - Defaut.png' % (scenar, year)

    def computeFunCourbesScenarYear(self, courbes, indVar, scenario, annee, allCourbes):
        default = self.defaults[scenario].get(annee)
        if default is None:
            # défaut trié par le max de puissance sur la période
            default = sorted(self.extractDefault(courbes), key=lambda x: x[1])
            self.defaults[scenario][annee] = default

        if len(default) == 0 and indVar != 0:
            return "-"
        if indVar == 0:
            # Plot les défauts!
            if not self.options.get('noGraph', False):
                if len(default) == 0:
                    typeD = "-"
                    hour = 0
                    puissT = "0"
                    siT = ""
                    puiss = 1
                    total = "0"
                else:
                    typeD = 'Sur production' if default[0][0] < 0 else 'Sous production'
                    hour = default[0][1]
                    puissT = eng_string(default[0][2], format="%0.2f", si=True)
                    total = eng_string(np.sum([el[2] for el in default]), format="%0.2f", si=True)
                    if self.siT is None:
                        siT, puiss = eng_string(default[0][2], si=True, onlySI=True)
                        self.siT = siT
                        self.puiss = puiss
                    else:
                        siT = self.siT
                        puiss = self.puiss

                plt.title(self.graphOptions['title'].format(scenario=scenario,
                                                            annee=annee, puiss=puissT, typeD=typeD, hour=hour, total=total))
                courbe_norm = courbes / puiss
                #axes = plt.gca()
                #axes.set_ylim([0, 100])
                plt.ylabel('Puissance en %sW' % (siT))
                plt.xlabel('Index horaire - 0 correspond au 1er janvier à 00h00')
                if self.graphOptions['label'] is None:
                    lbl = 'Defaut'
                else:
                    lbl = self.graphOptions['label'].format(
                        scenario=scenario, annee=annee, puiss=puissT, typeD=typeD, hour=hour, total=total)
                plt.plot(courbe_norm, label=lbl)
                plt.legend(loc='best')

            if len(default) == 0:
                return "-"

            # Type de défaut
            return 'Sur production' if default[0][0] < 0 else 'Sous production'
        elif indVar == 1:
            # Nombre d'heure consécutives du plus long défaut de l'année
            return default[0][1]
        elif indVar == 2:
            # Energie total du plus long défaut de l'année (GWh)
            return default[0][2] / 10**9
        elif indVar == 3:
            "Énergie totale des défauts sur l'année (GWh)"
            return np.sum([el[2] for el in default]) / 10**9

    @staticmethod
    def test_creation_default(courbes, seuilP=82, seuilN=-60):
        courbe1 = np.sum(list(courbes.values()), axis=0)
        nPmin = float(np.min(courbe1))
        courbe1 = rollingMin(courbe1, 7 * 24)
        m = np.min(courbe1)
        M = np.max(courbe1)
        courbe1 = np.add(courbe1, -m)
        courbe1 *= 200 / (M - m)
        courbe1 = np.add(courbe1, -100)
        defaultP = (courbe1 - seuilP)
        defaultP[defaultP < 0] = 0
        defaultN = (courbe1 - seuilN)
        defaultN[defaultN > 0] = 0
        default = defaultP + defaultN
        default[np.isnan(default)] = 0
        plt.plot(default)
        return default

    @staticmethod
    def test_extract_default():
        d = extract_default(default)
        max([(el[1], el[2], el[3]) for el in d if el[0] == 1])

    @staticmethod
    def extract_kdeparam(default, courbe_default, all_e=True, positif=True, invertPuiss=False):
        X = []
        Y = []
        for el in default:
            if not all_e and ((el[0] != 1 and positif) or (el[0] != -1 and not positif)):
                continue
            X += [el[1]] * el[1]
            coeff = -1 if invertPuiss else 1
            Y += list(coeff * courbe_default[el[3]:el[3] + el[1]])
        return X, Y

    @staticmethod
    def plot_kde_scenar(courbes_default, colorsMaps):
        extr_d = []
        for ind, c in enumerate(courbes_default):
            print(" ====== %d ======= " % ind)
            default = extract_default(c)
            extr_d.append(default)
            X, Y = extract_kdeparam(default, c)
            if len(X) == 0 or len(X) != len(Y):
                print("No default for courbes index %d" % ind)
            ax = sns.kdeplot(X, Y, cmap=colorsMaps[ind], legend=True, shade=True, shade_lowest=False)

    @staticmethod
    def max_defaut(courbes, scenario, annee, typeFun, varname, invertP=False, positif=True, plotOnlyMax=False, color='Reds', **kwargs):
        index = 1 if positif else -1
        default = extract_default(courbes)
        default = [el for el in default if el[0] == index]
        if len(default) == 0:
            print("No Default")
            return "-"

        M = max(default, key=lambda el: el[2])
        if plotOnlyMax:
            X, Y = extract_kdeparam([M], courbes)
        else:
            X, Y = extract_kdeparam(default, courbes)

        if len(X) == 0 or len(X) != len(Y):
            print("No default for courbes index %d" % ind)
            return '-'

        try:
            ax = sns.kdeplot(X, Y, cmap=color, legend=True, shade=True, shade_lowest=False)
            save_graph(scenario + '%s - %d  - %s sur %s.png' % (scenario, annee, typeFun, varname), **kwargs)
        except (ValueError, np.linalg.linalg.LinAlgError) as e:
            print("ERROR in Plot : %s" % e)
            print(X, Y)
        return "%sW / %s heures" % (eng_string(-M[2] if positif ^ invertP else M[2], format="%0.6f", si=True), M[1])

    @staticmethod
    def test_plot_default_kde():
        # cd={k: creation_default({'t':c}) for k, c in courbes.items()}
        # sns.set(style="darkgrid")
        # plot_kde_scenar(cd.values(), ['Greys', 'Purples', 'Blues', 'Greens', 'Oranges', 'Reds',
        #            'YlOrBr', 'YlOrRd', 'OrRd', 'PuRd', 'RdPu', 'BuPu',
        #            'GnBu', 'PuBu', 'YlGnBu', 'PuBuGn', 'BuGn', 'YlGn','binary', 'gist_yarg', 'gist_gray', 'gray', 'bone'])

        X, Y = extract_kdeparam(d, default, False)
        ax = sns.kdeplot(X, Y, cmap='Reds', legend=True, shade=True, shade_lowest=False)
        X, Y = extract_kdeparam(d, default, False, False)
        ax = sns.kdeplot(X, Y, cmap='Blues', legend=True, shade=True, shade_lowest=False)


class StatsDefaultGraph3Years(StatsDefault):

    def computeGraphFilename(self, ind, scenar, year):
        return '%s.png' % (scenar)

    def clearCurrentGraph(self, indVar, scenar, year):
        return indVar == 0 and scenar is not None and year is None

    def saveCurrentGraph(self, indVar, scenar, year):
        return indVar == 0 and scenar is not None and year is None


class FonctionnementNucGaz(BasicIndicateur):
    VAR_NUC = "Nucleaire"
    VAR_GAZ = "Gaz"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.name = "Fonctionnement nucléaire ou gaz"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # force no graphics
        self.options['noGraph'] = True

    def getRowHeader(self, index):
        # Il ne devrait y avoir qu'une seule "variables"
        return "Fonctionnement nucléaire/gaz (nombre d'heure)"

    def computeFunCourbesScenarYear(self, courbes, indVar, scenario, annee, allCourbes):
        return np.sum(np.logical_or(courbes[self.VAR_NUC] > 0, courbes[self.VAR_GAZ] > 0))

    @staticmethod
    def test_kwargs(datas):
        courbes = datas['perspective_2017']
        (nuc, gaz) = FonctionnementNucGaz.creation_nuc_gaz(courbes)
        d = {'SCENAR1': {2015: {FonctionnementNucGaz.VAR_NUC: nuc, FonctionnementNucGaz.VAR_GAZ: gaz}}}
        scenarios = ['SCENAR1']
        years = [2015]
        variables = [[FonctionnementNucGaz.VAR_NUC, FonctionnementNucGaz.VAR_GAZ]]
        return {
            'variables': variables,
            'scenarios': scenarios,
            'years': years,
            'datas': d,
            'filenameCSV': "test/FonctionnementNucGaz.csv",
        }

    @staticmethod
    def creation_nuc_gaz(courbes, seuilP=82, seuilN=-60):
        courbe1 = np.sum(list(courbes.values()), axis=0)
        nPmin = float(np.min(courbe1))
        courbe1 = rollingMin(courbe1, 7 * 24)
        m = np.min(courbe1)
        M = np.max(courbe1)
        courbe1 = np.add(courbe1, -m)
        courbe1 *= 200 / (M - m)
        courbe1 = np.add(courbe1, -100)
        defaultP = (courbe1 - seuilP)
        defaultP[defaultP < 0] = 0
        defaultN = (courbe1 - seuilN)
        defaultN[defaultN > 0] = 0
        defaultP[np.isnan(defaultP)] = 0
        defaultN[np.isnan(defaultN)] = 0
        gaz = -defaultN
        nuc = defaultP
        return (nuc, gaz)


class FacteurCharge(BasicIndicateur):
    VAR_DISP_PMAX = "disp_pmax"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.name = "Facteur de charge (%)"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # force no graphics
        self.options['noGraph'] = True

    def computeFunCourbesScenarYear(self, courbes, indVar, scenario, annee, allCourbes):
        summation = np.sum(courbes)
        pmax_th = allCourbes[self.VAR_DISP_PMAX][self.variables[indVar]] * 10**6

        if pmax_th == 0:
            if summation != 0:
                raise ValueError("Pmax théorique == 0 mais sum(puissance, an) != 0 !!")
            return "-"
        # Facteur de charge en %
        return "%0.1f" % ((summation * 100) / (len(courbes) * pmax_th))

    @staticmethod
    def test_kwargs(datas):
        courbes = datas['perspective_2017']
        variables = ['transport_cars', 'res_eq', 'ind_bz', 'ind_ca', 'ind_cb', 'ind_cc', 'ind_cd',
                     'ind_ce', 'ind_cf', 'ind_cg', 'ind_ch', 'ind_ci', 'ind_cj', 'ind_ck', 'ind_cl', 'ind_cm']
        # Ajout d'un disp_pmax
        courbes[FacteurCharge.VAR_DISP_PMAX] = {k: np.max(courbes[k]) / 10**6 for k in variables}

        d = {'SCENAR1': {2015: courbes}}
        scenarios = ['SCENAR1']
        years = [2015]

        return {
            'variables': variables,
            'scenarios': scenarios,
            'years': years,
            'datas': d,
            'filenameCSV': "test/FacteurCharge.csv",
            'options': {'Y': 'scenaryear'},
        }


class FacteurChargeOnly(FacteurCharge):

    def getRowHeader(self, index):
        return self.varNames[index]

    def headerCSV(self):
        if self.options.get('Y', "variables") == "variables":
            headers = ["Facteur de charge (%) / Scénario - Années"] + ["Scénario %s / Année %s" %
                                                                       (scenar, annee) for scenar in self.scenarios for annee in self.years]
        else:
            headers = ["Scénario - Années / Facteur de charge (%)"] + self.varNames

        return headers


class SommeAnnuelle(BasicIndicateur):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # force no graphics
        self.options['noGraph'] = True
        self.name = "Somme annuelle (TWh)"

    def computeFunCourbesScenarYear(self, courbes, indVar, scenario, annee, allCourbes):
        summation = np.sum(courbes)
        # Retour en terawatt
        return summation / 10**12

    @staticmethod
    def test_kwargs(datas):
        courbes = datas['perspective_2017']
        d = {'SCENAR1': {2015: courbes}}
        scenarios = ['SCENAR1']
        years = [2015]
        variables = ['total_demand']
        return {
            'variables': variables,
            'scenarios': scenarios,
            'years': years,
            'datas': d,
            'filenameCSV': "test/SommeAnnuel.csv",
            'graphOptions': {'base_path': "test/"},
        }

    def afterCSV(self, typeEvent='', var=None, scenar=None, year=None):
        if typeEvent == 'var':
            # A newline
            self.saveCSV([])


class SommeAnnuelleCondSign(BasicIndicateur):

    def __init__(self, *args, **kwargs):
        super().__init__(*args,  **kwargs)
        self.signe = (kwargs.get("signe", 1) >= 0)
        self.nbLineBefore = kwargs.get("nbLineBefore", 0)
        self.nbLineAfter = kwargs.get("nbLineAfter", 0)

        self.name = "Somme annuelle - éléments %s - (TWh)" % ("positif" if self.signe else "négatif")

        # force no graphics
        self.options['noGraph'] = True

    def computeFunCourbesScenarYear(self, courbes, indVar, scenario, annee, allCourbes):
        if self.signe:
            summation = np.sum(courbes[courbes >= 0])
        else:
            summation = -np.sum(courbes[courbes <= 0])
        # Retour en terawatt
        return summation / 10**12

    @staticmethod
    def test_kwargs(datas):
        courbes = datas['perspective_2017']
        d = {'SCENAR1': {2015: courbes}}
        scenarios = ['SCENAR1']
        years = [2015]
        variables = ['total_demand']
        return {
            'variables': variables,
            'scenarios': scenarios,
            'years': years,
            'datas': d,
            'signe': -1,
            'nbLineAfter': 2,
            'nbLineBefore': 3,
            'filenameCSV': "test/SommeAnnuel.csv",
            'graphOptions': {'base_path': "test/"},
        }

    def afterCSV(self, typeEvent='', var=None, scenar=None, year=None):
        if typeEvent == 'var':
            # A newline
            for ind in range(self.nbLineAfter):
                self.saveCSV([])

    def beforeCSV(self, typeEvent='', var=None, scenar=None, year=None):
        if typeEvent == 'var':
            # A newline
            for ind in range(self.nbLineBefore):
                self.saveCSV([])


def total_pilote_an(delta):
    return np.sum(delta[delta > 0])


def delta_pilotable(delta, nom_pilotable, scenario):
    nPmax = float(np.max(delta))
    #plt.legend(loc='upper right')
    plt.title('%s - histogramme puissance piloté de %s - Pmax piloté: %sW' %
              (scenario, nom_pilotable, eng_string(nPmax, format="%0.2f", si=True)))
    siT, puiss = eng_string(nPmax, si=True, onlySI=True)
    courbe_norm = delta / puiss
    #axes = plt.gca()
    #axes.set_ylim([0, 100])
    plt.xlabel('Puissance en %sW' % (siT))
    plt.ylabel("Nombre d'heures")
    plt.hist(courbe_norm[courbe_norm != 0], bins=100)


def test_delta_pilotable():
    import pickle
    with open('WS/lissage.pickle', 'rb') as my_file_obj:
        lissage = pickle.load(my_file_obj)

    delta_pilotable(lissage['deltas']['pilotale_res_ter_heating'], 'pilotale_res_ter_heating', 'SCENAR')
    delta_pilotable(lissage['deltas']['pilotable_transport_cars'], 'pilotable_transport_cars', 'SCENAR')
    delta_pilotable(lissage['deltas']['pilotable_res_ecs'], 'pilotable_res_ecs', 'SCENAR')
    delta_pilotable(lissage['deltas']['pilotable_res_eq'], 'pilotable_res_eq', 'SCENAR')
    for k, c in lissage['deltas'].items():
        print("Total piloté sur l'année pour %s : %sW" % (k, eng_string(total_pilote_an(c), format="%0.4f", si=True)))


def default_somme(dCourbes, scenario, annee, typeFun, varname, var=None, **kwargs):
    diff = 0
    for k, el in dCourbes.items():
        diff += kwargs['coeffs'][k] * np.sum(el)

    print("Difference : %d => %0.4f" % (diff, diff * 100 / (np.sum(dCourbes["total_demand"]))))


class InterCo(BasicIndicateur):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.name = "Interco"
        graphOptions = {
            'title': '{scenario}/{annee} - Interco - max: {pmax}W',
            'label': None,
        }
        graphOptions.update(self.graphOptions)
        self.graphOptions = graphOptions

    def computeFunCourbesScenarYear(self, courbes, indVar, scenario, annee, allCourbes):
        interco = np.sum(list(courbes.values()), axis=0)
        nPmax = float(np.max(interco))
        if not self.options.get('noGraph', False):
            plt.title(self.graphOptions['title'].format(scenario=scenario,
                                                        annee=annee, pmax=eng_string(nPmax, format="%0.2f", si=True)))
            if self.siT is None:
                siT, puiss = eng_string(nPmax, si=True, onlySI=True)
                self.siT = siT
                self.puiss = puiss
            else:
                siT = self.siT
                puiss = self.puiss
            courbe_norm = interco / puiss
            #axes = plt.gca()
            #axes.set_ylim([0, 100])
            plt.ylabel('Puissance en %sW' % (siT))
            plt.xlabel('Index horaire - 0 correspond au 1er janvier à 00h00')
            if self.graphOptions['label'] is None:
                lbl = 'Puissance'
            else:
                lbl = self.graphOptions['label'].format(
                    scenario=scenario, annee=annee, pmax=eng_string(nPmax, format="%0.2f", si=True))
            plt.plot(courbe_norm, label=lbl)
            plt.legend(loc='best')

        return nPmax

    def getRowHeader(self, index):
        # Il ne devrait y avoir qu'une seule "variables"
        return "Pmax"

    def computeGraphFilename(self, ind, scenar, year):
        return '%s - %d  - Interco.png' % (scenar, year)

    @staticmethod
    def test_kwargs(datas):
        raise NotImplemented("Not Yet")
        courbes = datas['perspective_2017']
        d = {'SCENAR1': {2015: courbes}}
        scenarios = ['SCENAR1']
        years = [2015]
        variables = [list(courbes.keys())]
        return {
            'variables': variables,
            'scenarios': scenarios,
            'years': years,
            'datas': d,
            'name': "P-MIN",
            'filenameCSV': "test/Pmin.csv",
            'graphOptions': {'base_path': "test/"},
        }


class InterCoGraph3Years(InterCo):

    def computeGraphFilename(self, ind, scenar, year):
        return '%s.png' % (scenar)

    def clearCurrentGraph(self, indVar, scenar, year):
        return indVar is not None and scenar is not None and year is None

    def saveCurrentGraph(self, indVar, scenar, year):
        return indVar is not None and scenar is not None and year is None


class MoyennageDeltaInterCo(BasicIndicateur):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.name = "Moyennage glissant des Delta Interco (7j)"
        graphOptions = {
            'width': 7 * 24,
            'title': '{scenario}/{annee} - DeltaIntero - Pmax: {pmax}W',
            'label': None,
            'label_sum': None,
            'width_label': '7 jours',
            'with_sum': False,
        }
        graphOptions.update(self.graphOptions)
        self.graphOptions = graphOptions

    def computeFunCourbesScenarYear(self, courbes, indVar, scenario, annee, allCourbes):
        nPmax = float(np.max(courbes))
        if not self.options.get('noGraph', False):
            plt.title(self.graphOptions['title'].format(scenario=scenario,
                                                        annee=annee, pmin=eng_string(nPmax, format="%0.2f", si=True)))
            if self.siT is None:
                siT, puiss = eng_string(nPmax, si=True, onlySI=True)
                self.siT = siT
                self.puiss = puiss
            else:
                siT = self.siT
                puiss = self.puiss
            courbe_norm = courbes / puiss
            #axes = plt.gca()
            #axes.set_ylim([0, 100])
            plt.ylabel('Puissance en %sW' % (siT))
            plt.xlabel('Index horaire - 0 correspond au 1er janvier à 00h00')
            if self.graphOptions['label'] is None:
                lbl = 'Puissance moyenne sur ' + self.graphOptions['width_label'] + ' glissants'
            else:
                lbl = self.graphOptions['label'].format(
                    scenario=scenario, annee=annee, pmax=eng_string(nPmax, format="%0.2f", si=True))
            plt.plot(rollingMean(courbe_norm, self.graphOptions['width']), label=lbl)
            if self.graphOptions['with_sum']:
                if self.graphOptions['label_sum'] is None:
                    lbl = 'Puissance'
                else:
                    lbl = self.graphOptions['label_sum'].format(
                        scenario=scenario, annee=annee, pmax=eng_string(nPmax, format="%0.2f", si=True))
                plt.plot(courbe_norm, label=lbl)
            plt.legend(loc='best')

        return nPmax

    def getRowHeader(self, index):
        # Il ne devrait y avoir qu'une seule "variables"
        return "Pmax"

    def computeGraphFilename(self, ind, scenar, year):
        return '%s - %d  - Delta interco (moyenne glissante sur 7jours).png' % (scenar, year)

    @staticmethod
    def test_kwargs(datas):
        raise NotImplemented("Not Yet")
        courbes = datas['perspective_2017']
        d = {'SCENAR1': {2015: courbes}}
        scenarios = ['SCENAR1']
        years = [2015]
        variables = [list(courbes.keys())]
        return {
            'variables': variables,
            'scenarios': scenarios,
            'years': years,
            'datas': d,
            'name': "P-MIN",
            'filenameCSV': "test/Pmin.csv",
            'graphOptions': {'base_path': "test/"},
        }


class MoyennageDeltaInterCoGraph3Years(MoyennageDeltaInterCo):

    def computeGraphFilename(self, ind, scenar, year):
        return '%s.png' % (scenar)

    def clearCurrentGraph(self, indVar, scenar, year):
        return indVar is not None and scenar is not None and year is None

    def saveCurrentGraph(self, indVar, scenar, year):
        return indVar is not None and scenar is not None and year is None


class DispNucExport(BasicIndicateur):
    VAR_DISP_PMAX = "disp_pmax"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.name = "Disponibilité nucléaire à l'export"
        self.max_interco = kwargs.get('max_interco', 17e9)

        # force no graphics
        self.options['noGraph'] = True

    def getRowHeader(self, index):
        # Il ne devrait y avoir qu'une seule "variables"
        return "Disponibilité nucléaire à l'export(TWh)"

    def getHeaderLabels(self):
        return ("Indicateur", "Variables")

    def computeFunCourbesScenarYear(self, courbes, indVar, scenario, annee, allCourbes):
        # On passe pas de courbes
        listpilot = ['Fioul', 'Charbon', 'Nucleaire', 'Gaz', 'UIOM', 'Biomasse']
        temp = allCourbes['max_envelope_disp'] * allCourbes[self.VAR_DISP_PMAX]['Nucleaire'] / \
            np.sum(allCourbes[self.VAR_DISP_PMAX][el] for el in listpilot)
        disp_nuc = np.maximum(temp - np.ndarray.flatten(allCourbes['Nucleaire']), 0)
        dispinterco = self.max_interco - allCourbes['intercoraw'] + allCourbes['deltainterco']
        return np.sum(np.minimum(disp_nuc, dispinterco)) / 1e12

    @staticmethod
    def test_kwargs(datas):
        raise NotImplemented("Not Yet")
        courbes = datas['perspective_2017']
        variables = ['transport_cars', 'res_eq', 'ind_bz', 'ind_ca', 'ind_cb', 'ind_cc', 'ind_cd',
                     'ind_ce', 'ind_cf', 'ind_cg', 'ind_ch', 'ind_ci', 'ind_cj', 'ind_ck', 'ind_cl', 'ind_cm']
        # Ajout d'un disp_pmax
        courbes[DispNucExport.VAR_DISP_PMAX] = {k: np.max(courbes[k]) / 10**6 for k in variables}

        d = {'SCENAR1': {2015: courbes}}
        scenarios = ['SCENAR1']
        years = [2015]

        return {
            'variables': variables,
            'scenarios': scenarios,
            'years': years,
            'datas': d,
            'filenameCSV': "test/DispNucExport.csv",
        }


def compute_heatmap_abs(mydict):
    mystore = {}
    mymeanstore = {}
    mymax = {'pv': 0.2, 'wind': 0.2}
    mysize = 10
    for scenar, years in mydict.items():
        mystore[scenar] = {}
        for year, myvars in years.items():
            mystore[scenar][year] = np.zeros((mysize, mysize))
            for i_w in range(mysize):
                for i_pv in range(mysize):
                    c_w = (mymax['wind'] / mysize) * i_w
                    c_pv = (mymax['pv'] / mysize) * i_pv
                    disp = np.minimum(c_w * myvars['disp_pmax']['wind_onshore'] * 1e6, myvars['wind_onshore']
                                      ) + np.minimum(c_pv * myvars['disp_pmax']['pv'] * 1e6, myvars['pv'])
                    mywhere = np.where(myvars['default_sure'] < 0)
                    mystore[scenar][year][i_w, i_pv] = np.sum(
                        disp[mywhere[0]] - np.maximum((disp + myvars['default_sure'])[mywhere[0]], 0)) / 1e12
        mymeanstore[scenar] = (mystore[scenar][2012] + mystore[scenar][2013] + mystore[scenar][2015]) / 3
        mymeanstore[scenar] = pd.DataFrame({(mymax['wind'] * myvars['disp_pmax']['wind_onshore'] / 1e3 / mysize) * i: mymeanstore[scenar][:, i] for i in range(mysize)}, index=[i * mymax['pv'] * myvars['disp_pmax']['pv'] / 1e3 / mysize for i in range(mysize)])
        # mystore[scenar][year].index.names = [i * mymax['pv'] / mysize * 100 for i in range(mysize)]
        mymeanstore[scenar].columns.name = "Puissance d'éolien terrestre pilotable en GW"
        mymeanstore[scenar].index.name = "Puissance de solaire pilotable en GW"
        f, ax = plt.subplots(figsize=(9, 6))
        sns.heatmap(mymeanstore[scenar], annot=True, linewidths=.5, ax=ax)
        plt.title("Défauts annuels évitables (en TWh) en fonction de la puissance de solaire et d'éolien pilotable - " + scenar)
        path = 'Graphs/'
        f.savefig(path + scenar + ' - Défauts évitables en fonction du renouvelable pilotable' + '.png', dpi=100)
        plt.clf()
    return mymeanstore


def compute_heatmap(mydict):
    mystore = {}
    mymeanstore = {}
    mymax = {'pv': 0.5, 'wind': 0.5}
    mysize = 10
    for scenar, years in mydict.items():
        mystore[scenar] = {}
        for year, myvars in years.items():
            mystore[scenar][year] = np.zeros((mysize, mysize))
            for i_w in range(mysize):
                for i_pv in range(mysize):
                    c_w = (mymax['wind'] / mysize) * i_w
                    c_pv = (mymax['pv'] / mysize) * i_pv
                    disp = c_w * myvars['wind_onshore'] + c_pv * myvars['pv']
                    mywhere = np.where(myvars['default_sure'] < 0)
                    mystore[scenar][year][i_w, i_pv] = np.sum(
                        disp[mywhere[0]] - np.maximum((disp + myvars['default_sure'])[mywhere[0]], 0)) / 1e12

        mymeanstore[scenar] = (mystore[scenar][2012] + mystore[scenar][2013] + mystore[scenar][2015]) / 3
        mymeanstore[scenar] = pd.DataFrame({(mymax['wind'] * 100 / mysize) * i: mymeanstore[scenar][:, i] for i in range(mysize)}, index=[i * mymax['pv'] * 100 / mysize for i in range(mysize)])

        # mystore[scenar][year] = pd.DataFrame({(mymax['wind'] / mysize) * i * 100: mystore[scenar][year][:, i] for i in range(mysize)}, index=[i * mymax['pv'] / mysize * 100 for i in range(mysize)])
        # mystore[scenar][year].index.names = [i * mymax['pv'] / mysize * 100 for i in range(mysize)]
        mymeanstore[scenar].columns.name = "% d'éolien terrestre pilotable"
        mymeanstore[scenar].index.name = "% de solaire pilotable"
        f, ax = plt.subplots(figsize=(15, 10))
        sns.heatmap(mymeanstore[scenar], annot=True, linewidths=.5, ax=ax)
        plt.title("Défauts annuels évitables (en TWh) en fonction de la puissance de solaire et d'éolien pilotable en % - " + scenar)
        path = 'Graphs/'
        f.savefig(path + scenar + ' - Défauts évitables en fonction de la fraction du renouvelable pilotable' + '.png', dpi=100)
        plt.clf()
    return mystore


def distrib_delta_interco(mydict):
    mystore = {}
    myvars = {'deltainterco': 'Pilotage des interconnexions',
              'net_demand': 'Demande nette des EnR variables',
              'default_sure': 'Défaut',
              'total_demand': 'Demande brute totale'}
    df = {}
    for scenar, years in mydict.items():
        mystore[scenar] = {}
        for myvar in myvars.keys():
            temp = [mydict[scenar][year][myvar] for year in years]
            temp = np.concatenate(temp, axis=0)
            mystore[scenar][myvar] = temp
        df[scenar] = pd.DataFrame({name: mystore[scenar][myvar] for myvar, name in myvars.items()})
    return df


class PieChartRepartitionSummation(BasicIndicateur):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.noCSV = True

        self.name = "Répartition"
        self.coeffs = kwargs.get("coeffs", [])
        self.metavars = kwargs.get("metavars", [])

    def computeFunCourbesScenarYear(self, courbes, indVar, scenario, annee, allCourbes):
        # max index of demand total

        f, axarr = self.get_plot(courbes, indVar, scenario, annee)

        maxidxs = self._get_indexes(courbes, indVar, scenario, annee, allCourbes)
        useval = max(len(maxidxs), 1)

        # get sum at maxind of list of curves
        listvals = []
        for ind, c in enumerate(courbes):
            if ind < len(self.coeffs):
                sign = self.coeffs[ind]
            else:
                sign = 1

            tempval = 0
            for myvar in c.values():
                tempval += myvar[maxidxs].sum()
            listvals.append(sign * tempval / useval)
        listvals = self.postTraitVals(listvals)
        sumlistvals = sum(listvals)

        def absolute_value(val):
            a = np.round(val / 100. * sumlistvals, 0)
            return str(a / 1e9)[:4]

        axarr.pie(listvals, explode=[0.05 for el in self.metavars],
                  colors=sns.color_palette("hls", 8), autopct=absolute_value,
                  shadow=True, startangle=140)
        title = self.getTitle(indVar, scenario, annee, maxidxs, listvals)
        axarr.set_title(title)
        axarr.axis('equal')

    def postTraitVals(self, listvals):
        return listvals

    def computeVarNames(self):
        self.varNames = ["var %d" % (ind) for ind, var in enumerate(self.variables)]
        self.varNamesCSV = ["var %d" % (ind) for ind, var in enumerate(self.variables)]

    def beforeLineCSV(self, var=None, scenar=None, year=None):
        pass

    def afterLineCSV(self, var=None, scenar=None, year=None):
        pass


class PieChart3YearsMixIn(Graph3YearsMixIn):

    def beforeCSV(self, typeEvent='', var=None, scenar=None, year=None):
        if typeEvent == "annee":
            # construct subplot
            f, axarr = plt.subplots(1, len(self.years), squeeze=False)
            print('XXXXXX', type(axarr), axarr.shape, type(axarr[0]))
            self.f = f
            plt.suptitle(self.generaltitle.format(var=var, scenar=scenar, year=year), fontsize=self.fontsize)
            self.f.subplots_adjust(hspace=1.5)
            self.axarr = {self.years[ind]: axarr[0, ind] for ind in range(len(self.years))}
            f.set_size_inches(12.3, 4)

    def clearGraph(self):
        super().clearGraph()
        plt.close(self.f)

    def afterCSV(self, typeEvent='', var=None, scenar=None, year=None):
        if typeEvent == "annee":
            plt.tight_layout()
            plt.subplots_adjust(right=0.75)
            plt.legend(self.metavars, loc="center right", bbox_to_anchor=(2, .5))

    def get_plot(self, courbes, indVar, scenario, annee):
        return self.f, self.axarr[annee]


class PieChartAllYears(PieChart3YearsMixIn, PieChartRepartitionSummation):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "generaltitle" not in kwargs:
            self.generaltitle = 'Répartition de la consommation pour le maximum de demande\n{scenar}'
        self.fontsize = 18

    def _get_indexes(self, courbes, indVar, scenario, annee, allCourbes):
        return [np.argmax(allCourbes['total_demand'])]

    def getTitle(self, indVar, scenario, annee, maxidxs, listvals):
        # return self.graphOptions['title'].format(scenario=scenario, annee=annee,
        # maxidxs=maxidxs, lmaxidxs=len(maxidxs), )
        return '\n\nMétéo {annee} - H {idx} - {idx24}h - {sumval:.0f}GW'.format(annee=annee, idx=maxidxs[0], idx24=maxidxs[0] % 24, sumval=sum(listvals) / 1e9)


class PieChartMeanAllYears(PieChart3YearsMixIn, PieChartRepartitionSummation):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fontsize = 18
        self.nmean = 90
        if "generaltitle" not in kwargs:
            self.generaltitle = 'Répartition moyenne de la consommation pour les ' + \
                str(self.nmean) + ' heures de plus forte demande\n{scenar}'

    def _get_indexes(self, courbes, indVar, scenario, annee, allCourbes):
        return allCourbes['total_demand'].argsort()[-self.nmean:][::-1]

    def getTitle(self, indVar, scenario, annee, maxidxs, listvals):
        # return self.graphOptions['title'].format(scenario=scenario, annee=annee,
        # maxidxs=maxidxs, lmaxidxs=len(maxidxs), )
        return '\n\nMétéo {annee} - {sumval:.0f}GW'.format(annee=annee, sumval=sum(listvals) / 1e9)


class PieChartDefaultAllYears(PieChart3YearsMixIn, PieChartRepartitionSummation):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fontsize = 18
        if "generaltitle" not in kwargs:
            self.generaltitle = 'Répartition moyenne des variables pour les heures de défaut\n{scenar}'

    def _get_indexes(self, courbes, indVar, scenario, annee, allCourbes):
        return np.where(allCourbes['default_sure'] > 0)[0]

    def getTitle(self, indVar, scenario, annee, maxidxs, listvals):
        # return self.graphOptions['title'].format(scenario=scenario, annee=annee,
        # maxidxs=maxidxs, lmaxidxs=len(maxidxs), )
        return '\n\nMétéo {annee} - {sumval:.0f}GW - {defaults} défauts'.format(annee=annee, sumval=sum(listvals) / 1e9, defaults=len(maxidxs))


class PieChartDefaultProductionAllYears(PieChartDefaultAllYears):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "generaltitle" not in kwargs:
            self.generaltitle = 'Répartition moyenne de la production pour les heures de défaut\n{scenar}'


class PieChartDefaultDemandAllYears(PieChartDefaultAllYears):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "generaltitle" not in kwargs:
            self.generaltitle = 'Répartition moyenne de la consommation pour les heures de défaut\n{scenar}'
