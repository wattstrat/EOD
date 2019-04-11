import os
import pickle

from Calculus.GraphCsvZip.Indicators import Pmax, PminEnRGraph3Years, StatsDefaultGraph3Years, FacteurChargeOnly
from Calculus.GraphCsvZip.Indicators import SommeAnnuelle, InterCoGraph3Years, MoyennageDeltaInterCoGraph3Years
from Calculus.GraphCsvZip.Indicators import DispNucExport, SommeAnnuelleCondSign, GraphVariablesGraph3Years
from Calculus.GraphCsvZip.Indicators import PieChartDefaultProductionAllYears, PieChartDefaultDemandAllYears
from Calculus.GraphCsvZip.Indicators import PieChartMeanAllYears, PieChartAllYears

from Calculus.calculus import Calculus

# Création des directories


class FolderADEME(Calculus):

    def __init__(self, mysimuid, *args, **kwargs):
        super().__init__(*args, **kwargs)
        dirs = ['DOSSIER',
                'DOSSIER/Defauts',
                'DOSSIER/Defauts/graphiques annuels - résolution horaire',
                'DOSSIER/Defauts/répartition demande - heures de défauts',
                'DOSSIER/Defauts/répartition offre - heures de défauts',
                'DOSSIER/Demande totale',
                'DOSSIER/Description des pointes de consommation',
                'DOSSIER/Description des pointes de consommation/répartition demande - pointe de conso',
                'DOSSIER/Description des pointes de consommation/répartition demande - 90 heures de conso max',
                'DOSSIER/Interco',
                # 'DOSSIER/Interco/forcage des intercos - moyenne glissante',
                'DOSSIER/Pilotage de la demande',
                'DOSSIER/Puissance minimale EnR']

        if 'rootpath' in kwargs:
            self.rootpath = kwargs['rootpath']
            if self.rootpath[-1] != '/':
                self.rootpath += '/'
        else:
            self.rootpath = ""

        self.rootpath += 'Temporary/' + mysimuid + '/'
        try:
            os.makedirs(self.rootpath)
        except FileExistsError:
            # May exist
            pass
        for D in dirs:
            try:
                os.mkdir(self.rootpath + D)
            except FileExistsError:
                # May exist
                pass

    def _run(self, datas):
        scenarios = list(datas.keys())
        years = list(next(iter(datas.values())).keys())

        # Configuration des CSV/Graph
        listvarsdemand = [
            ['agr'],
            ['ind_bz', 'ind_ca', 'ind_cb', 'ind_cc', 'ind_cd', 'ind_ce', 'ind_cf',
                'ind_cg', 'ind_ch', 'ind_ci', 'ind_cj', 'ind_ck', 'ind_cl', 'ind_cm'],
            ['internal_conso', 'losses'],
            ['res_aircond', 'res_cooking', 'res_ecs', 'res_eq', 'res_lighting', 'res_airing'],
            ['res_heating'],
            ['ter_aircond', 'ter_eq',  'ter_lighting'],
            ['ter_heating'],
            ['transport_cars', 'transport_other']
        ]
        list_metavars_demand = [
            'Agriculture',
            'Industrie',
            'Pertes et consommation interne',
            'Residentiel hors chauffage',
            'Chauffage résidentiel',
            'Tertiaire hors chauffage',
            'Chauffage tertiaire',
            'Transport'
        ]
        listvarsprod = [
            ['hydro_run', 'hydrolake', 'hydrostep', ],
            ['pv'],
            ['wind_onshore', 'wind_offshore'],
            ['intercoraw', 'deltainterco'],
            ['Nucleaire'],
            ['Gaz'],
            ['UIOM',  'Biomasse'],
            ['pilotable_transport_cars', 'pilotable_ind', 'pilotable_res_eq',
                'pilotable_res_ecs', 'pilotable_res_ter_heating', 'pilotable_batterie']
        ]

        list_metavars_prod = [
            'Hydro',
            'PV',
            'Éoliens',
            'Imports',
            'Nucleaire',
            'Gaz',
            'Autres',
            'Pilotage de la demande'
        ]
        configDossier = {
            self.rootpath + 'DOSSIER/Pmax.csv': [
                Pmax(
                    variables=['total_demand', 'net_demand', 'demand_to_match'],
                    scenarios=scenarios,
                    years=years,
                    datas=datas,
                    options={'noGraph': True}
                )
            ],
            # self.rootpath + 'DOSSIER/DispoNucExport.csv': [
            #     SommeAnnuelle(
            #         variables=['nuc_exp'],
            #         scenarios=scenarios,
            #         years=years,
            #         datas=datas,
            #         options={'noGraph': True}
            #     )
            # ],
            self.rootpath + 'DOSSIER/FacteurCharge.csv': [
                FacteurChargeOnly(
                    variables=['Charbon', 'Fioul', 'Gaz', 'Nucleaire', 'Biomasse', 'UIOM', 'pv', 'wind_onshore',
                               'wind_offshore', 'hydro_run'],
                    scenarios=scenarios,
                    years=years,
                    datas=datas,
                    options={'Y': 'scenarannee',
                             'noGraph': True}
                ),
            ],
            self.rootpath + 'DOSSIER/Mix_elec.csv': [
                SommeAnnuelle(
                    variables=[
                        'total_demand',
                        'tot_interco',
                    ],
                    scenarios=scenarios,
                    years=years,
                    datas=datas,
                    options={'closeCSV': False,
                             'noGraph': True}
                ),
                SommeAnnuelle(
                    variables=[
                        'Nucleaire',
                        'Gaz',
                        'Charbon',
                        'Fioul',
                        'UIOM',
                        'Biomasse',
                    ],
                    scenarios=scenarios,
                    years=years,
                    datas=datas,
                    options={'closeCSV': False,
                             'noGraph': True}
                ),
                SommeAnnuelle(
                    variables=[
                        'hydrolake',
                        'hydrostep',
                    ],
                    scenarios=scenarios,
                    years=years,
                    datas=datas,
                    options={'closeCSV': False,
                             'noGraph': True}
                ),
                SommeAnnuelle(
                    variables=[
                        'hydro_run',
                        'wind_onshore',
                        'wind_offshore',
                        'pv',
                    ],
                    scenarios=scenarios,
                    years=years,
                    datas=datas,
                    options={'closeCSV': False,
                             'noGraph': True}
                ),
                SommeAnnuelle(
                    variables=[
                        'default_sure',
                    ],
                    scenarios=scenarios,
                    years=years,
                    datas=datas,
                    options={'closeCSV': True,
                             'noGraph': True}
                ),
                SommeAnnuelleCondSign(
                    variables=[
                        'default_sure',
                    ],
                    scenarios=scenarios,
                    years=years,
                    datas=datas,
                    signe=-1,
                    nbLineBefore=3,
                    options={'closeCSV': True,
                             'noGraph': True}
                ),
            ],
            self.rootpath + 'DOSSIER/defauts_surprod_max.csv': [
                StatsDefaultGraph3Years(
                    variables=['default_sure'],
                    scenarios=scenarios,
                    years=years,
                    datas=datas,
                    graphOptions={
                        'title': '{scenario} - Defaut',
                        'label': 'Meteo {annee} - {total}W',
                        'base_path': self.rootpath + 'DOSSIER/Defauts/graphiques annuels - résolution horaire/'
                    }
                ),
            ],
            None: [
                GraphVariablesGraph3Years(
                    variables=['total_demand'],
                    scenarios=scenarios,
                    years=years,
                    datas=datas,
                    options={'noCSV': True},
                    graphOptions={
                        'title': '{scenario} - {varname} en {si}W',
                        'label': '{annee}',
                        'base_path': self.rootpath + 'DOSSIER/Demande totale/'
                    }
                ),
                PminEnRGraph3Years(
                    variables=[['pv',
                                'wind_onshore',
                                'wind_offshore',
                                'hydro_run', ]],
                    scenarios=scenarios,
                    years=years,
                    datas=datas,
                    options={'noCSV': True},
                    graphOptions={
                        'title': '{scenario} - Enr - Pmin glissant sur 7 jours',
                        'label': '{annee} - Pmin: {pmin}W',
                        'base_path': self.rootpath + 'DOSSIER/Puissance minimale EnR/'
                    }
                ),
                InterCoGraph3Years(
                    variables=[['intercoraw', 'deltainterco']],
                    scenarios=scenarios,
                    years=years,
                    datas=datas,
                    options={'noCSV': True},
                    graphOptions={
                        'title': '{scenario} - Interco',
                        'label': '{annee} - max: {pmax}W',
                        'base_path': self.rootpath + 'DOSSIER/Interco/'
                    }
                ),
                # MoyennageDeltaInterCoGraph3Years(
                #     variables=['deltainterco'],
                #     scenarios=scenarios,
                #     years=years,
                #     datas=datas,
                #     options={'noCSV': True},
                #     graphOptions={
                #         'title': '{scenario} - Delta Interco (moyenne glissante sur 7 jours)',
                #         'label': '{annee} - max: {pmax}W',
                #         'base_path': self.rootpath + 'DOSSIER/Interco/forcage des intercos - moyenne glissante/'}
                # ),
                PieChartAllYears(
                    variables=[listvarsdemand],
                    scenarios=scenarios,
                    years=years,
                    datas=datas,
                    metavars=list_metavars_demand,
                    graphOptions={
                        'base_path': self.rootpath + 'DOSSIER/Description des pointes de consommation/répartition demande - pointe de conso/'}
                ),
                PieChartMeanAllYears(
                    variables=[listvarsdemand],
                    scenarios=scenarios,
                    years=years,
                    datas=datas,
                    metavars=list_metavars_demand,
                    graphOptions={
                        'base_path': self.rootpath + 'DOSSIER/Description des pointes de consommation/répartition demande - 90 heures de conso max/'}
                ),

                PieChartDefaultDemandAllYears(
                    variables=[listvarsdemand],
                    scenarios=scenarios,
                    years=years,
                    datas=datas,
                    metavars=list_metavars_demand,
                    graphOptions={
                        'base_path': self.rootpath + 'DOSSIER/Defauts/répartition demande - heures de défauts/'}
                ),
                PieChartDefaultProductionAllYears(
                    variables=[listvarsprod],
                    scenarios=scenarios,
                    years=years,
                    datas=datas,
                    metavars=list_metavars_prod,
                    coeffs=[1, 1, 1, -1, 1, 1, 1, -1],
                    graphOptions={
                        'base_path': self.rootpath + 'DOSSIER/Defauts/répartition offre - heures de défauts/'}
                ),
                GraphVariablesGraph3Years(
                    variables=[['pilotable_transport_cars', 'pilotable_ind', 'pilotable_res_eq',
                                'pilotable_res_ecs', 'pilotable_res_ter_heating', 'pilotable_batterie']],
                    scenarios=scenarios,
                    years=years,
                    datas=datas,
                    options={'noCSV': True},
                    window=(0, 200),
                    graphOptions={
                        'title': 'Pilotage agrégé de la demande - 200 premières heures - {scenario}',
                        'label': 'Météo {annee} - max conso déplacée {minpositif}W',
                        'additionalText': {
                            'args': (100, -1e10, 'négatif = effacement, positif = report'),
                            'kwargs': {'verticalalignment': 'bottom', 'horizontalalignment': 'center', 'fontsize': 10},
                        },
                        'base_path': self.rootpath + 'DOSSIER/Pilotage de la demande/'
                    }
                ),
            ],
        }
        # Création des fichiers du Dossier
        for fichier, lIndicateurs in configDossier.items():
            print('+ File: %s' % (fichier if fichier is not None else '[GRAPH]'))
            ret = {
                'writerCSV': None,
                'filenameCSV': fichier
            }
            for Indicateur in lIndicateurs:
                print(' - %s' % Indicateur.name)
                Indicateur.init(ret.get('writerCSV'), ret.get('filenameCSV'), ret.get('hFileCSV'))
                ret = Indicateur.compute()
