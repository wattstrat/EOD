#import ot
import numpy as np


class DemandPilotable:

    pilotable = {
        'pilotable_transport_cars': [{'var': 'transport_cars', 'coeff': 0.2}],
        'pilotable_res_ecs': [{'var': 'res_ecs', 'coeff': 0.5}],
        'pilotable_res_ter_heating': [{'var': 'res_heating', 'coeff': 0.2}, {'var': 'ter_heating', 'coeff': 0.2}],
        'pilotable_res_eq': [{'var': 'res_eq', 'coeff': 0.2}],
        'pilotable_ind': [
            {'coeff': 0.2, 'var': 'ind_bz'},
            {'coeff': 0.2, 'var': 'ind_ca'},
            {'coeff': 0.2, 'var': 'ind_cb'},
            {'coeff': 0.2, 'var': 'ind_cc'},
            {'coeff': 0.2, 'var': 'ind_cd'},
            {'coeff': 0.2, 'var': 'ind_ce'},
            {'coeff': 0.2, 'var': 'ind_cf'},
            {'coeff': 0.2, 'var': 'ind_cg'},
            {'coeff': 0.2, 'var': 'ind_ch'},
            {'coeff': 0.2, 'var': 'ind_ci'},
            {'coeff': 0.2, 'var': 'ind_cj'},
            {'coeff': 0.2, 'var': 'ind_ck'},
            {'coeff': 0.2, 'var': 'ind_cl'},
            {'coeff': 0.2, 'var': 'ind_cm'}],
        'pilotable_batterie': [{'fun': lambda x: np.full(x, 0), 'coeff': 1}]
    }

    nb_hour = 8760

    contraintes = {
        'pilotable_transport_cars': {
            'pic_horaire': [np.full(nb_hour, -2 * 10**9), np.full(nb_hour, 2 * 10**9)],
            'max_an': 0,  # 8 * 10**12,
            'sumcumulwindow': True,
            'maxannuel': False,
            'conservation': True,
            'rescalepic': True,
            'seuilPilotable': None,
        },
        'pilotable_res_ecs': {
            'pic_horaire': [np.full(nb_hour, -3 * 10**9), np.full(nb_hour, 3 * 10**9)],
            'max_an': 0,  # 3.5 * 10**12,
            'sumcumulwindow': True,
            'maxannuel': False,
            'conservation': True,
            'rescalepic': True,
            'seuilPilotable': None,
        },
        'pilotable_res_ter_heating': {
            'pic_horaire': [np.full(nb_hour, -1 * 10**9), np.full(nb_hour, 1 * 10**9)],
            'max_an': 0,  # 17.5 * 10**12,
            'sumcumulwindow': True,
            'maxannuel': False,
            'conservation': True,
            'rescalepic': True,
            'seuilPilotable': None,
        },
        'pilotable_res_eq': {
            'pic_horaire': [np.full(nb_hour, -0.5 * 10**9), np.full(nb_hour, 0.5 * 10**9)],
            'max_an': 0,  # 4 * 10**12,
            'sumcumulwindow': True,
            'maxannuel': False,
            'conservation': True,
            'rescalepic': True,
            'seuilPilotable': None,
        },
        'pilotable_ind': {
            'pic_horaire': [np.full(nb_hour, -3 * 10**9), np.full(nb_hour, 3 * 10**9)],
            'max_an': 0,
            'sumcumulwindow': True,
            'maxannuel': False,
            'conservation': True,
            'rescalepic': True,
            'seuilPilotable': 50e9,

        },
        'pilotable_batterie': {
            'pic_horaire': [np.full(nb_hour, -1 * 10**9), np.full(nb_hour, 1 * 10**9)],
            'sumcumulwindow': True,
            'maxannuel': False,
            'conservation': False,
            'rescalepic': True,
            'coeff_consommation': np.full(nb_hour, 1.2),
            'coeff_production': np.full(nb_hour, 1),
            'max_cumul_pos': 10**9,
            'max_cumul_neg': 0,
            'seuilPilotable': None,
        }
    }

    window_width = 24

    def __init__(self, width=None, matriceTransfert=False, val_min_pic=None, val_max_pic=None, max_an=None):
        if width is not None:
            self.window_width = width

        if val_min_pic is not None:
            for k, val in val_min_pic.items():
                if type(val) is np.ndarray:
                    if val.shape != (self.nb_hour,):
                        raise ValueError("%s != %s for %s in val_min_pic" % (val.shape, (self.nb_hour,), k))
                    self.contraintes[k]['pic_horaire'][0] = val
                elif type(val) not in [float, int]:
                    raise TypeError("val_min_pic is not a float, int or ndarray for %s" % k)
                else:
                    self.contraintes[k]['pic_horaire'][0] = np.full(self.nb_hour, val, dtype=np.float64)

        if val_max_pic is not None:
            for k, val in val_max_pic.items():
                if type(val) is np.ndarray:
                    if val.shape != (self.nb_hour,):
                        raise ValueError("%s != %s for %s in val_max_pic" % (val.shape, (self.nb_hour,), k))
                    self.contraintes[k]['pic_horaire'][1] = val
                elif type(val) not in [float, int]:
                    raise TypeError("val_max_pic is not a float, int or ndarray for %s" % k)
                else:
                    self.contraintes[k]['pic_horaire'][1] = np.full(self.nb_hour, val, dtype=np.float64)
        if max_an is not None:
            for k, val in max_an.items():
                if type(val) not in [float, int]:
                    raise TypeError("max_an is not a float or int for %s" % k)
                else:
                    self.contraintes[k]['max_an'] = val

        #self.transfert = matriceTransfert
        self.stockages = ['pilotable_batterie']

    def GetLissage(self, courbes):
        cp = self.construct_pilotable(courbes)
        # Exlude stockage CF warning inside function
        s = self.construct_target(courbes, cp, self.stockages)
        # TODO boucle IA descente gradient:
        #  + 1) génération 1 séparation de Sum(pilotable) par pilotable
        #    - contrainte qui doivent être OK concernant la conservation
        #    - contrainte qui doivent être OK concernant le déplacement sur 1 an
        #    - contrainte qui doivent être OK concernant le déplacement sur 1 heure
        #    - contrainte sur la longueur du déplacement
        #    => erreur par rapport à total_target
        #  + tant que optim pas fini
        #     + OT (self.constructTransfertMatrice)
        #     + vérif des contraintes précédente sur la matrice
        #       - pas OK => 1)
        #     + cout des courbes construites (erreur(sum(pilotable) / total_target_pilotable))
        #     + descente de gradient pour trouver une nouvelle séparation
        #        des pilotables vérifiant les contrainte

        # Stockage en plus!
        # Construct delta of total: total[H+1]-total[H]
        # Finalement, pas besoin : sur total conso
        #deltaH1m1 = s['total'][1:]-s['total'][:-1]
        #s['deltaH1'] = np.append(deltaH1m1, deltaH1m1[-1])

        target_pilotables = self.constr_target_pilotable(s, cp, self.stockages)

        pilotables_lisses = np.sum(list(target_pilotables.values()), axis=0)
        batt = {
            # Meme objectif lissé
            'target_pilotable': s['target_pilotable'],
            # Le pilotable actuel:
            'pilotable': pilotables_lisses,
            #'deltaH1': s['deltaH1']
        }
        target_pilotable_stockage = self.constr_target_pilotable(
            batt, cp, [k for k in self.contraintes.keys() if k not in self.stockages])
        pilotables_tot_lisses = np.sum(list(target_pilotable_stockage.values()) + [pilotables_lisses], axis=0)
        target_pilotables.update(target_pilotable_stockage)

        # if self.transfert:
        #     matrices=self.constructTransfertMatrice(cp, target_pilotable)
        #     s['transfertMatrices'] = matrices
        s['pilotables'] = cp
        s['target_pilotables'] = target_pilotables
        s['total_lisse'] = pilotables_tot_lisses + s['non_pilotable']
        s['deltas'] = {k: c - cp[k] for k, c in target_pilotables.items()}
        self.result = s
        return s

    def construct_pilotable(self, courbes):
        courbes_pilotable = {}
        for key in self.pilotable.keys():
            courbes_pilotable[key] = np.zeros(self.nb_hour, dtype=np.float64)
            for elm in self.pilotable[key]:
                if 'fun' in elm:
                    courbes_pilotable[key] += (elm['coeff'] * elm['fun'](self.nb_hour))
                else:
                    courbes_pilotable[key] += (elm['coeff'] * courbes[elm['var']])
        return courbes_pilotable

    @staticmethod
    def sliding_average(courbe, N=24):
        if N % 2 != 0:
            raise
        augm_courbe = np.concatenate((np.array([courbe[0]] * int(N / 2)), courbe, np.array([courbe[-1]] * int(N / 2))))
        lenC = len(augm_courbe)
        step = 2 * int(N / 2)
        return np.sum(np.array([augm_courbe[k:lenC - (step - k)] for k in range(0, step)]), axis=0) / step

    def construct_target(self, courbes, courbes_pilotable, exludes):
        constr = {}
        constr['total'] = np.sum(list(courbes.values()), axis=0)

        constr['pilotable'] = np.sum([el for k, el in courbes_pilotable.items() if k not in excludes], axis=0)
        constr['non_pilotable'] = constr['total'] - constr['pilotable']
        # Target : moyenne sur un jour glissant
        constr['target'] = DemandPilotable.sliding_average(constr['total'], self.window_width)
        constr['target_pilotable'] = constr['target'] - constr['non_pilotable']
        #### WARNING #####
        # On prend pas en compte les stockages dans les courbes de charges
        # Pour le moment, batterie => on considère qu'elle est à 0
        # Dans le cas d'une consommation de veille, à voir comment l'intégré
        # *) dans le total donnée, donc dès le début
        # *) à postériori => à rajouter dans les courbes non pilotable? le target_pilotable?
        #     => pour Flo, c'est non pilotable car la consommation y sera et on peut rien y faire.
        return constr

    def constr_target_pilotable(self, target, courbes_pilotable, excludes=[]):
        target_pilotable = {}
        funCap = [max, min]
        deltas = target['target_pilotable'] - target['pilotable']

        pic_horaires_mod = {}
        for k, el in self.contraintes.items():
            if k in excludes:
                continue
            pic_horaires_mod[k] = [np.copy(el['pic_horaire'][0]), np.copy(el['pic_horaire'][1])]
            if el['seuilPilotable'] is None:
                continue
            # Non pilotable par delta sur h+1
            # non_pilotable = (np.abs(target['deltaH1']) < el['seuilPilotable'])
            # Pilotage si total > seuil
            non_pilotable = (target['total'] < el['seuilPilotable'])
            pic_horaires_mod[k][0][non_pilotable] = 0
            pic_horaires_mod[k][1][non_pilotable] = 0

        max_deltas = [np.sum([el[ind] for k, el in pic_horaires_mod.items()], axis=0) for ind in range(2)]
        pilotable = {k: np.zeros(self.nb_hour) for k in self.contraintes.keys() if k not in excludes}
        for ind, delta in enumerate(deltas):
            if delta == 0:
                # No need to pilot or don't want to
                continue
            indPic = 0 if (delta < 0) else 1
            for k, el in pic_horaires_mod.items():
                pilotable[k][ind] = funCap[indPic](el[indPic][ind], el[indPic][ind] * delta / max_deltas[indPic][ind])

        # On coefficiente la conso/prod (cf batteries)
        for k, deltaEl in pilotable.items():
            # Ajout des coeffs
            if 'coeff_consommation' in self.contraintes[k]:
                deltaEl[deltaEl > 0] *= self.contraintes[k]['coeff_consommation'][deltaEl > 0]
            if 'coeff_production' in self.contraintes[k]:
                deltaEl[deltaEl < 0] *= self.contraintes[k]['coeff_production'][deltaEl < 0]

        # sum cumul pilotable[k] = 0 sur la taille de la fenetre
        for k, el in pilotable.items():
            if not self.contraintes[k].get('sumcumulwindow', False):
                continue
            moy = DemandPilotable.sliding_average(el, self.window_width)
            el -= moy
            print("erreur standart de la moyenne sur %d heure par rapport à  0 pour %s : %f" %
                  (self.window_width, k, moy.std()))
        # sum pilotable[k] (el positif) <= max_an
        for k, el in pilotable.items():
            if not self.contraintes[k].get('maxannuel', False):
                continue
            # Renormalisation si sum pilotable[k] (el positif) > max_an
            cumul = np.sum(el[el > 0])
            if cumul <= self.contraintes[k]['max_an']:
                continue
            print("Renormalisation annuel obligatoire pour %s" % (k))
            coeff = self.contraintes[k]['max_an'] / cumul
            pilotable[k] = coeff * pilotable[k]

        for k, c in pilotable.items():
            target_pilotable[k] = courbes_pilotable[k] + pilotable[k]

        # sum target_pilotable = sum pilotable réelle
        for k in pilotable.keys():
            if not self.contraintes[k].get('conservation', False):
                continue
            sum_annuelle = np.sum(courbes_pilotable[k])
            delta_annuel = sum_annuelle - np.sum(target_pilotable[k])
            target_pilotable[k] += delta_annuel / self.nb_hour

        # Rescaling pour ne pas dépasser sur les heures
        for k, c in target_pilotable.items():
            if not self.contraintes[k].get('rescalepic', False):
                continue
            p = c - courbes_pilotable[k]
            minC, maxC = np.min(p), np.max(p)

            #maxCurrent=max(-minC, maxC)
            minA, maxA = np.min(self.contraintes[k]['pic_horaire']), np.max(self.contraintes[k]['pic_horaire'])
            #maxAllowed=max(-minA, maxA)
            if minA <= minC and maxC <= maxA:
                continue

            coeff = min(maxA / maxC, minA / minC)
            print("Dépassement des contraintes pour %s : %f <= %f,%f <= %f | coeff correcteur: %f" %
                  (k, minA, minC, maxC, maxA, coeff))
            p *= coeff
            target_pilotable[k] = courbes_pilotable[k] + p

        return target_pilotable

    def constructTransfertMatrice(self, cp, target_pilotable):
        retMat = {}
        cout = self.constructMatriceCout()
        for k in cp.keys():
            retMat[k] = ot.emd(cp[k], target_pilotable[k], cout)
            # TODO traitement de non possible
        return retMat

    def constructMatriceCout(self):
        # TODO
        raise


class TotalDemandPilotable(DemandPilotable):

    def construct_target(self, courbes, courbes_pilotable, excludes):
        constr = {}
        constr['total'] = courbes['net_demand']
        constr['pilotable'] = np.sum([el for k, el in courbes_pilotable.items() if k not in excludes], axis=0)
        constr['non_pilotable'] = constr['total'] - constr['pilotable']
        # Target : moyenne sur un jour glissant
        constr['target'] = DemandPilotable.sliding_average(constr['total'], self.window_width)
        constr['target_pilotable'] = constr['target'] - constr['non_pilotable']
        return constr
