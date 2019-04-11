import numpy as np
from Utils.Numpy import rollingMax, rollingMin, rollingMean
import pickle

refpmax = {'hydrolake': 9159, 'hydrostep': 5184}


class HydroPilotable:
    window_width = 72
    nb_hour = 8760
    pic_pilotable_2 = {
        'hydro_lake': [np.full(nb_hour, 0), np.full(nb_hour, 9159.0 * 10**6)],
        'hydro_step': [np.full(nb_hour, -5184.0 * 10**6), np.full(nb_hour, 5184.0 * 10**6)]
    }

    data_hydro = {}

    def __init__(self, newpmax=refpmax):

        # getting data for hydro: static
        with open('Scripts/hydrodatas.pickle', 'rb') as f:
            self.data_hydro = pickle.load(f)

        for key in self.data_hydro:
            self.data_hydro[key] = self.data_hydro[key] * newpmax[key] / refpmax[key]
        self.renorm_data_hydro()

    def GetLissage(self, demand):
        dem_retrend = self.remove_trend(demand)
        target_dem = HydroPilotable.sliding_average(dem_retrend, self.window_width)
        target_hydro = self.constr_absorb_hydro(target_dem, dem_retrend)
        reconstr_target_hydro = {k: target_hydro[k] + courbe for k, courbe in self.trend.items()}
        final_hydro = self.ecretage(reconstr_target_hydro)

        dem_lisse = demand - np.sum(list(final_hydro.values()), axis=0)

        obt = (target_dem - dem_lisse).std()
        nol = (target_dem - demand).std()
        print("Diff d'ecart standart avec le non lissé : %f" % ((nol - obt) / nol))

        return final_hydro

    def ecretage(self, reconstr_target_hydro):
        # TODO : faire l'ecretage via le pic_pilotable_2
        # Erreur lake:
        print("Erreur lake: %d hours < 0" % np.sum(reconstr_target_hydro['hydrolake'] < 0))
        # Ecretage
        reconstr_target_hydro['hydrolake'][reconstr_target_hydro['hydrolake'] < 0] = 0
        return reconstr_target_hydro

    @staticmethod
    def sliding_average(courbe, N=24):
        if N % 2 != 0:
            raise
        augm_courbe = np.concatenate((np.array([courbe[0]] * int(N / 2)), courbe, np.array([courbe[-1]] * int(N / 2))))
        lenC = len(augm_courbe)
        step = 2 * int(N / 2)
        return np.sum(np.array([augm_courbe[k:lenC - (step - k)] for k in range(0, step)]), axis=0) / step

    def renorm_data_hydro(self):
        courbes = {}
        minmax = {}
        trend = {}
        for k, c in self.data_hydro.items():
            trend[k] = HydroPilotable.sliding_average(c, self.window_width)
            courbes[k] = c - trend[k]
            minmax[k] = [
                rollingMin(courbes[k], 3 * self.window_width),
                rollingMax(courbes[k], 3 * self.window_width)
            ]
        self.trend = trend
        self.pic_pilotable = minmax
        self.delta_hydro = courbes

    def remove_trend(self, demand):
        return demand - np.sum(list(self.trend.values()), axis=0)

    def constr_absorb_hydro(self, target, original):
        funCap = [max, min]
        deltas = target - original
        max_deltas = [np.sum([el[ind] for k, el in self.pic_pilotable.items()], axis=0) for ind in range(2)]
        pilotable = {k: np.zeros(self.nb_hour) for k in self.pic_pilotable.keys()}
        for ind, delta in enumerate(deltas):
            if delta == 0:
                # No need to pilot
                continue
            # WARNING: c'est de la prod !!! INVERSE DE LA DEMANDE
            # delta > 0 => on doit augmenter la consommation de la prod, ie diminuer sa production!
            indPic = 0 if (delta > 0) else 1
            for k, el in self.pic_pilotable.items():
                # le delta est de signe opposé à max_delta => le coeff doit etre positif => -delta
                pilotable[k][ind] = funCap[indPic](el[indPic][ind], el[indPic][ind] * -delta / max_deltas[indPic][ind])

        # sum cumul pilotable[k] = 0 sur la taille de la fenetre
        for k, el in pilotable.items():
            moy = HydroPilotable.sliding_average(el, self.window_width)
            el -= moy
            print("erreur standart de la moyenne sur %d heure par rapport à  0 pour %s : %f" %
                  (self.window_width, k, moy.std()))

        # Rescaling pour ne pas dépasser sur les heures
        for k, c in pilotable.items():
            minC, maxC = np.min(c), np.max(c)

            minA, maxA = np.min(self.pic_pilotable[k]), np.max(self.pic_pilotable[k])
            if minA <= minC and maxC <= maxA:
                continue

            coeff = min(maxA / maxC, minA / minC)
            print("Dépassement des contraintes pour %s : %f <= %f,%f <= %f | coeff correcteur: %f" %
                  (k, minA, minC, maxC, maxA, coeff))
            c *= coeff
            pilotable[k] = c

        return pilotable
