import numpy as np
from scipy.optimize import minimize
import multiprocessing
import warnings

import cvxopt
from cvxopt import matrix, solvers
solvers.options['show_progress'] = False

import pdb

warnings.simplefilter('error', RuntimeWarning)
"""
TODO : 
    Facile :
        Enlever les couts dynamiques des stations qui démarrent.  
        Parallelisation de cvxopt ?
        DONE : Ajouter cout constant à avoir une techno allumée, et éteinte.
        Verifications sur le gradient (notamment le q pas utilisé, voir commentaire)
    Moyen :
        Essayer la perte linéaire pour la prediction des couts d'allumage
        Amelioration du point initial avec algo de Djikstra
        Acceleration de la procedure en utilisant le probleme dual pour eliminer des cas

    Difficile :
        Faire par centrale
        Prediction avec plusieurs heures d'avance
        Faire l'optimisation des couts de démarrage et extinction, et les couts statiques/dynamiques en meme temps

"""
npool = 20

START_FAC = 1
COST_FRAC = 1e5
speed2coef = 5
threshold = [0.1, 0.05, 0.2, -np.inf, -np.inf, -np.inf]
off_values = np.array([0.005, 0.012, 0.05, 0., 0., 0.])


def all_subsets(s):
    """
    Return all the possible subsets of the set s
    """
    if len(s) == 0:
        return [s]
    x = s.pop()
    subsets_without_x = all_subsets(s)
    subsets_with_x = [ss | {x} for ss in subsets_without_x]
    return subsets_without_x + subsets_with_x


def project_on_hyperplan(z, value, metric):
    """
    Return the projection of the vector z on the affine 
    hyperplan given by <x,(1,1,...,1)> = value, according to the 
    diagonal metric given by metric
    This could be used for the initial point of the timestep 
    optimisation
    """
    pz = z + (value - z.sum()) / metric.sum() * metric
    return pz


def project_on_cube(z, k_min, k_max):
    """
    Return the projection of z on the cube given 
    by k_min_i <= z_i <= k_max_i for all i.
    This could be used for the initial point of the timestep 
    optimisation
    """
    return np.clip(z, k_min, k_max)


###############################
# These are auxilliary functions used for
# multiprocessing
def _fun(t):
    timesteppred, seqk = t
    return timesteppred.grad_staticdynamiccosts(seqk)


def _fun2(ts):
    r, _ = ts.minimize_costs()
    return r


def _fun3(t):
    timesteppred, seqk = t
    return timesteppred.constraints_choiceconfig(seqk)


def _fun4(tt):
    timestepppred, target = tt
    r, _ = timestepppred.minimize_costs_oracle(target)
    return r
#################################


def minimizeIntersectionHalfspaces(G, h, x0, epsilon=1., verbose=0):
    """
    This compute an approximation of the problem : find a point x that
    intersects as many half spaces given by < G_i, x > <= h_i as possible

    Here we implemented a few relaxations of this problem : 
        * Quadratic : minimize Sum_i f(<G_i,x> - h_i)
            where f(x) = x**2 if x > 0
                         0 if x < 0
        * Exponential : minimize Sum_i f(<G_i,x> - h_i)
            where f(x) = exp(x)
        * Linear-exponential : minimize Sum_i f(<G_i,x> - h_i)
            where f(x) = gamma*x if x > 0
                         exp(gamma*x) - 1 if x < 0
    The best one seems to be the last one, but the solution is still to be improved

    For the last one, the hessian is not implemented, since there is a risk it is not well-defined 
    (we could try to implement it)
    I also try a simpler linear solution (f(x) = x if x > 0, 0 else), but did not work

    If you want to change the relaxation, you have to change the last
    lines of this function. The default algorithm does not use the hessian,
    if you choose an algorithm with a hessian, you need to choose the algorithm Newton-CG
    """
    def evaluatequad(x):
        Gx = np.dot(G, x)
        unsatisfied = Gx > h

        return ((Gx[unsatisfied] - h[unsatisfied]) ** 2).sum()

    def gradquad(x):
        Gx = np.dot(G, x)
        unsatisfied = Gx > h
        g = 2 * ((Gx[unsatisfied] - h[unsatisfied])[:, np.newaxis] * G[unsatisfied]).sum(axis=0)
        return g

    def hessquad(x):
        Gx = np.dot(G, x)
        unsatisfied = Gx > h
        if not np.any(unsatisfied):
            H = np.zeros((G.shape[1], G.shape[1]))
        else:
            H = 2 * np.dot(G[unsatisfied].T, G[unsatisfied])
        return H

    def evaluateexp(x):
        Gx = np.dot(G, x)
        return np.exp(Gx - h).sum()

    def gradexp(x):
        Gx = np.dot(G, x)
        return (G * np.exp(Gx - h)[:, np.newaxis]).sum(axis=0)

    def hessexp(x):
        f = np.exp(np.dot(G, x) - h)
        return sum(np.outer(G[i], G[i]) * f[i] for i in range(h.shape[0]))

    def evaluatelinexp(x):
        gamma = 1.
        Gx = np.dot(G, x)
        unsatisfied = Gx > h
        posf = gamma * (Gx[unsatisfied] - h[unsatisfied]).sum()
        negf = (np.exp(gamma * (Gx[~unsatisfied] - h[~unsatisfied])) - 1).sum()
        return posf + negf

    def gradlinexp(x):
        gamma = 1.
        Gx = np.dot(G, x)
        unsatisfied = Gx > h
        posgrad = gamma * G[unsatisfied].sum(axis=0)

        neggrad = (G[~unsatisfied] * np.exp(gamma * (Gx[~unsatisfied] - h[~unsatisfied]))[:, np.newaxis]).sum(axis=0)
        return posgrad + neggrad

    evaluate, grad = evaluatelinexp, gradlinexp  # , hessexp
    optimresult = minimize(evaluate, x0,  # method="Newton-CG",
                           jac=grad)  # , hess=hess)

    x = optimresult.x

    if verbose == 1:
        n_unsatisfied0 = sum(np.any(np.dot(G, x0) > h) for (G, h) in zip(Glist, hlist))
        n_unsatisfied = sum(np.any(np.dot(G, x) > h) for (G, h) in zip(Glist, hlist))
        print("Number of constraints : ", len(Glist))
        print("Starting score : ", evaluate(x0))
        print("Starting unsatisfied : ", n_unsatisfied0)
        print("Final score : ", evaluate(x))
        print("Final unsatisfied : ", n_unsatisfied)

    return x


def minimizeIntersectionPolytopes(Glist, hlist, x0, epsilon=1., gamma=1,
                                  lr=1., optimsteps=500, verbose=0):
    """
    This compute an approximation of the problem : find a point x that
    intersects as many half spaces given by < G_i, x > <= h_i as possible

    Here we implemented a few relaxations of this problem : 
        * Quadratic : minimize Sum_i f(<G_i,x> - h_i)
            where f(x) = x**2 if x > 0
                         0 if x < 0
        * Exponential : minimize Sum_i f(<G_i,x> - h_i)
            where f(x) = exp(x)
        * Linear-exponential : minimize Sum_i f(<G_i,x> - h_i)
            where f(x) = gamma*x if x > 0
                         exp(gamma*x) - 1 if x < 0
    The best one seems to be the last one, but the solution is still to be improved

    For the last one, the hessian is not implemented, since there is a risk it is not well-defined 
    (we could try to implement it)
    I also try a simpler linear solution (f(x) = x if x > 0, 0 else), but did not work

    If you want to change the relaxation, you have to change the last
    lines of this function. The default algorithm does not use the hessian,
    if you choose an algorithm with a hessian, you need to choose the algorithm Newton-CG
    """

    def projpolytop(G, x, h, initproj=None):
        h_int = h - gamma
        P = 2 * np.identity(x.shape[0])
        q = - 2 * x

        P = cvxopt.sparse(matrix(P))
        q = matrix(q)
        G = cvxopt.sparse(matrix(G))
        h_int = matrix(h_int)
        G = G / np.max(h_int)
        h_int = h_int / np.max(h_int)
        if initproj is None:
            sol = solvers.qp(P, q, G, h_int)
        else:
            sol = solvers.qp(P, q, G, h, initvals={"x": matrix(initproj)})
        proj = np.array(sol['x'])[:, 0]

        return proj

    def evaluatequad(G, x, h, initproj=None):
        xproj = projpolytop(G, x, h)
        evaluation = np.linalg.norm(x - xproj) ** 2
        return evaluation, xproj

    def gradquad(G, x, h, initproj=None):
        xproj = projpolytop(G, x, h)
        g = 2 * (x - xproj)
        return g, xproj

    projlist = [None for _ in Glist]

    def evaluate(x):
        eval_proj = [evaluatequad(G, x, h, xproj) for (G, h, xproj) in zip(Glist, hlist, projlist)]
        evaluations = np.array([evaluation for evaluation, xproj in eval_proj])
        projlist[:] = [xproj for _, xproj in eval_proj]
        return np.mean(evaluations)

    def grad(x):
        grad_proj = [gradquad(G, x, h, xproj) for (G, h, xproj) in zip(Glist, hlist, projlist)]
        gradarr = np.array([grad for grad, _ in grad_proj])

        projlist[:] = [xproj for _, xproj in grad_proj]
        return np.mean(gradarr, axis=0)

    x = np.copy(x0)
    for s in range(optimsteps):
        n_unsatisfied = sum(np.any(np.dot(G, x) > h) for (G, h) in zip(Glist, hlist))
        print("Score {}\tConstraints : {}/{}".format(evaluate(x), n_unsatisfied, len(Glist)))
        x -= lr * grad(x)

    #optimresult = minimize(evaluate, x0, jac=grad)
    #x = optimresult.x

    if verbose == 1:
        n_unsatisfied0 = sum(np.any(np.dot(G, x0) > h) for (G, h) in zip(Glist, hlist))
        n_unsatisfied = sum(np.any(np.dot(G, x) > h) for (G, h) in zip(Glist, hlist))
        print("Number of constraints : ", len(Glist))
        print("Starting score : ", evaluate(x0))
        print("Starting unsatisfied : ", n_unsatisfied0)
        print("Final score : ", evaluate(x))
        print("Final unsatisfied : ", n_unsatisfied)

    return x


class RetroOptim(object):
    """
    If L(y,u) is a real function , and for all u, y -> L(y,u) is strictly
    convex, then it defines phi(u) = y* defined to minimize L(y,u)
    phi(u) = y* is caracterized by dy(L)(y*,u) = 0

    The problem is to find u such that we minimize l(phi(u)) where l is 
    a loss function, typically l(phi(u)) = \|phi(u) - y0\|^2 where y0 is
    the target.

    This class contains methods for this optimisation problem 
    """

    def __init__(self, L, G, H, dthetaG, initialisation):
        """
        Here, n is the dimension of y the variable, and m the dimension 
        of theta the parameter
        L: function 
            L(y,theta) -> float
            Loss function
        G: function
            G(y,theta) -> np.ndarray of shape (n,)
            Gradient of the function y -> L(y,theta)
        H: function 
            H(y,theta) -> np.ndarray of shape (n,n)
            Hessian of the function y -> L(y,theta)
            It must be positive definite
        dthetaG: function
            dthetaG(y,theta) -> np.ndarray of shape (n,m)
            Differential of theta -> G(y,theta)
        initialisation: function
            initialisation(theta) -> np.ndarray of shape (n,)
            Returns an heuristic for the loss minimisation problem 

        loss: function
            loss(y) -> float
            Evaluation of the variable
        gradloss: function
            gradloss(y) -> np.ndarray of shape (n,)
            Gradient of the loss
        """
        self.L = L
        self.G = G
        self.H = H
        self.dthetaG = dthetaG
        self.initialisation

        self.loss
        self.gradloss

    def loss(self, y, theta):
        return self.L(y, u)

    def minimize_loss(self, theta, init_value=None, method='Newton-CG'):
        if init_value is None:
            init_value = self.initialisation(theta)
        opt = optimize.minimize(self.L, init_value, jac=self.G, hess=self.H)
        y = opt.x
        return y

    def _jac(self, theta, y=None, inity=None):
        if y is not None:
            y = self.minimize_loss(theta, init_value=inity)
        dthetag = self.dthetaG(y, theta)
        h = self.H(y, theta)

        jac = - np.dot(h, dthetag)

        return jac, y

    def _grad(self, theta, **kwargs):
        jac, y = self._jac(theta, **kwargs)
        gloss = self.gradloss(y)
        grad = np.dot(jac.T, gloss)
        return grad, y

    def retrooptim(theta, maxstep=500, lr=1., verbose=0):

        step = 0
        y = None
        while step < maxstep:
            grad, y = self._grad(theta, inity=y)
            theta = theta - lr * grad

            if verbose == 1:
                print("Step: {}\tLoss : {.4f}".format(step, self.loss(y)))
        return theta


class TimeStepPrediction(object):
    """
    This class is used for the prediction of a single time step, and the 
    gradient of the parameters for a single hour.
    """
    epsilon = 1.
    alwayson = {3}

    def __init__(self, static_costs, dyn_costs, startup_costs,
                 switchoff_costs, const_costs, past,
                 power_on, asked, k_min, k_max, normalisation):
        """
        Initialise the object
        Parameters : 
            static_costs, dyn_costs, startup_costs, switchoff_costs : array
            They have the same size, and are the costs of the different powerplants

            past : array
            Has the same size. It is the production at the previous timestep for each powerplant

            power_on : set
            It is the set of the powerplants that were on at the previous timestep

            asked : float
            asked production for this timestep

            k_min, k_max : array
            minimum and maximum production for this time step

            normalisation : array
            The normalisation used for each powerplant. We need it for the optimisation
        """

        self.n_powerplant = static_costs.shape[0]
        self.static_costs = static_costs
        self.dyn_costs = dyn_costs
        self.startup_costs = startup_costs
        self.switchoff_costs = switchoff_costs
        self.const_costs = const_costs
        self.past = past

        self.k_min = k_min
        self.k_max = k_max
        self.asked = asked

        self.power_on = power_on
        self.power_off = set(range(self.n_powerplant)) - set(power_on)

        self.normalisation = normalisation

    def minimize_costs(self):
        """
        Main function for prediction. It compute hte optimal solution
        for a timestep.
        It returns a tuple : the minimal solution, and the minimal cost
        """
        # List all possible configurations

        possible_config = [self.alwayson | ss
                           for ss in all_subsets(set(range(self.n_powerplant)) - self.alwayson)]

        # Keep only config such that productions is possible

        possible_config = [config for config in possible_config if
                           sum(self.k_max[i] * self.normalisation[i] for i in config) >= self._askedconf(config)]

        min_cost = np.inf
        min_sol = None

        for config in possible_config:
            y, cost = self.minimize_costs_config(config)
            cost += self.cost_config(config)

            if cost < min_cost:
                min_cost = cost
                min_sol = y

        return min_sol, min_cost

    def minimize_costs_oracle(self, target):
        # List all possible configurations

        possible_config = [self.alwayson | ss
                           for ss in all_subsets(set(range(self.n_powerplant)) - self.alwayson)]
        possible_config = [config for config in possible_config if
                           sum(self.k_max[i] * self.normalisation[i] for i in config) >= self._askedconf(config)]

        # config given by the oracle
        config = get_power_on(target, self.k_min, self.k_max)
        # Keep only config such that productions is possible

        if not config in possible_config:

            askedconf = self._askedconf(config)
            minprod = np.dot(self.k_min, self.normalisation)
            maxprod = np.dot(self.k_max, self.normalisation)
            raise ValueError("config not in possible_config", possible_config, askedconf,
                             minprod, maxprod, config, self.k_max * self.normalisation,
                             self.k_min, * self.normalisation, self.asked)

        # productions of off given by the oracle
        yoff = np.zeros(target.shape)
        for i in range(self.n_powerplant):
            if not i in config:
                yoff[i] = target[i]

        y, cost = self.minimize_costs_config(config, yoff=yoff)
        cost += self.cost_config(config)
        return y, cost

    def _askedconf(self, config):
        """
        Return the asked production for a given config, by taking into
        account the non-zero production of power-off powerplants
        """
        setoff = list(set(range(self.n_powerplant)) - config)
        return self.asked - np.dot(self.normalisation[setoff], self.k_min[setoff] + off_values[setoff] * (self.k_max[setoff] - self.k_min[setoff]))
        # return self.asked - sum((self.k_min[i] + off_values[i] * (self.k_max[i] - self.k_min[i])) * self.normalisation[i]
        #        for i in set(range(self.n_powerplant)) - config)

    def cost_config(self, config):
        """
        Returns the startup cost for a new configuration
        """
        cost_switchon = sum(self.startup_costs[i] for i in config - self.power_on)
        cost_switchoff = sum(self.switchoff_costs[i] for i in self.power_on - config)
        cost_const = sum(self.const_costs[i] for i in config)
        return cost_switchoff + cost_switchon + cost_const

    def _starting_point(self, asked, static_costs, dyn_costs, past, k_max, k_min, normalisation, tol=1e-3):
        """
        Return a starting point for the optimisation problem
        """
        # REMARK : I tried complicated algorithms. This simpler one works, but we could do better

        ########
        # This is the Dykstra's projection algorithm
        # https://en.wikipedia.org/wiki/Dykstra%27s_projection_algorithm

        #x = past
        #p = np.zeros(x.shape)
        #q = np.zeros(x.shape)
        # while np.any(x > k_max) or np.any(x < k_min) or np.abs(x.sum() - asked) >  1e-3:
        #y = project_on_cube(x+p, k_min, k_max)
        #p = x + p - y
        #x = project_on_hyperplan(y+q, asked, dyn_costs)

        #q = y + q - x
        # Method of alterning projections
        #x = project_on_hyperplan(project_on_cube(x, k_min, k_max), asked, dyn_costs)
        #x = project_on_hyperplan(project_on_cube(x, k_min, k_max), asked, dyn_costs)

        # if not (np.any(x > k_max) or np.any(x < k_min) or np.abs(x.sum() - asked)):
        #    return x
        # else:
        return k_min + (asked - (k_min * normalisation).sum()) / ((k_max - k_min) * normalisation).sum() * (k_max - k_min)

    def check_constraints(self, y, tol=None):
        """
        Check that y checks all the constraints
        """
        if tol is None:
            tol = self.epsilon
        return np.all(y <= self.k_max + tol) and \
            np.all(y >= self.k_min - tol) and \
            np.abs((y * self.normalisation).sum() - self.asked) < tol

    def minimize_costs_config(self, config, yoff=None, reduceqp=False):
        listconfig = sorted(list(config))
        listpower_on = sorted(list(self.power_on))

        # Deduce the production of power off powerplant
        if yoff is None:
            y = np.zeros((self.n_powerplant,))
            for i in set(range(self.n_powerplant)) - config:
                y[i] = self.k_min[i] + off_values[i] * (self.k_max[i] - self.k_min[i])
        else:
            y = yoff

        askedconf = self.asked - (y * self.normalisation).sum()

        static_costsconf = self.static_costs[listconfig]
        dyn_costsconf = self.dyn_costs[listconfig]
        #dyn_costsconf = self.dyn_costs[listpower_on]
        k_maxconf, k_minconf = self.k_max[listconfig], self.k_min[listconfig]
        pastconf = self.past[listconfig]
        normalisationconf = self.normalisation[listconfig]

        # Compute the starting point
        y_startconf = self._starting_point(askedconf, static_costsconf,
                                           dyn_costsconf, pastconf, k_maxconf, k_minconf,
                                           normalisationconf)

        # if not self.check_constraints(y_start):
        #    raise ValueError("Constraints are not ok for starting point")

        P = 2 * np.diag(dyn_costsconf)
        q = static_costsconf - 2 * dyn_costsconf * pastconf
        P = P / dyn_costsconf.max()
        q = q / dyn_costsconf.max()
        P = cvxopt.sparse(matrix(P))
        q = matrix(q)

        A = self.normalisation[np.newaxis, listconfig] / askedconf
        b = np.array([1.])
        A = matrix(A)
        b = matrix(b)

        G = np.zeros((2 * len(config), len(config)))
        h = np.zeros((2 * len(config),))
        for i in range(len(config)):
            G[2 * i, i] = 1.
            G[2 * i + 1, i] = -1.
            h[2 * i] = k_maxconf[i]
            h[2 * i + 1] = - k_minconf[i]
        G = cvxopt.sparse(matrix(G))
        h = matrix(h)
        G = G / np.max(h)
        h = h / np.max(h)

        # if initvals is not None:
        # sol = solvers.qp(P, q, G, h, A, b, initvals={"x": matrix(y_startconf)})

        try:
            sol = solvers.qp(P, q, G, h, A, b, initvals={"x": matrix(y_startconf)})
            yconf = np.array(sol['x'])[:, 0]
            cost_qp = sol["primal objective"] * dyn_costsconf.max() + (dyn_costsconf * (pastconf ** 2)).sum()
        except ValueError:
            print("Bug in optim: we use initial value !")
            yconf = y_startconf
            cost_qp = 0.5 * np.dot(np.dot(np.array(matrix(P)), yconf), yconf) + np.dot(np.array(q)[:, 0], yconf)
            cost_qp = cost_qp * dyn_costsconf.max() + (dyn_costsconf * (pastconf ** 2)).sum()

        #yconf = np.array(sol['x'])
        y[listconfig] = yconf
        # cost_qp = sol["primal objective"] * dyn_costsconf.max() + \
        #    (dyn_costsconf * (pastconf ** 2)).sum()

        total_cost = cost_qp

        if not self.check_constraints(y):
            print("Constraints not ok for optimal solution : we use initial value !")
            yconf = y_startconf
            cost_qp = 0.5 * np.dot(np.dot(np.array(matrix(P)), yconf), yconf) + np.dot(np.array(q)[:, 0], yconf)
            cost_qp = cost_qp * dyn_costsconf.max() + (dyn_costsconf * (pastconf ** 2)).sum()
            y[listconfig] = yconf
        return y, total_cost

    def constraints_choiceconfig(self, trueprod):
        """
        Used to optimize the starting costs and poweroff costs.
        Returns Gon, Goff, h, which means that the costs need to check
        Gx < h in order to select the best model
        """
        # List all possible configurations
        possible_config = [self.alwayson | ss
                           for ss in all_subsets(set(range(self.n_powerplant)) - self.alwayson)]

        # Keep only config such that productions is possible

        possible_config = [config for config in possible_config if
                           sum(self.k_max[i] * self.normalisation[i] for i in config) >= self._askedconf(config)]

        costs = np.zeros((len(possible_config),))
        switchons = np.zeros((len(possible_config), self.n_powerplant))
        switchoffs = np.zeros((len(possible_config), self.n_powerplant))
        active = np.zeros((len(possible_config), self.n_powerplant))

        trueidx = None
        minvalue = np.inf
        for i, config in enumerate(possible_config):
            switchonset = config - self.power_on
            switchoffset = self.power_on - config
            switchons[i, list(switchonset)] = 1.
            switchoffs[i, list(switchoffset)] = 1.
            # Allactive powerplants
            active[i, list(config)] = 1.

            yconfig, cost = self.minimize_costs_config(config)
            costs[i] = cost

            if np.linalg.norm(yconfig - trueprod) < minvalue:
                trueidx = i
                minvalue = np.linalg.norm(yconfig - trueprod)

        otherconfigs = ~(np.arange(len(possible_config)) == trueidx)

        Gon = - switchons[otherconfigs] + switchons[trueidx]
        Goff = - switchoffs[otherconfigs] + switchoffs[trueidx]
        Gactive = - active[otherconfigs] + active[trueidx]
        h = costs[otherconfigs] - costs[trueidx]
        return Gon, Goff, Gactive, h

    def _grad_interiorconfig(self, y, interiorconfig, trueprod):
        """
        Compute the grad of static and dynamic costs in y, for the 
        real production trueprod, for the config in which y was
        """
        n = len(interiorconfig)
        listconfig = list(interiorconfig)

        P = 2 * np.diag(self.dyn_costs[listconfig])

        # WARING : q is never used : to be checked !!!
        q = self.static_costs[listconfig] - \
            2 * self.dyn_costs[listconfig] * self.past[listconfig]

        M = np.zeros((n, n - 1))
        for i in range(n - 1):
            M[i, i] = 1.

        Projnorm = np.outer(self.normalisation[listconfig], self.normalisation[
                            listconfig]) / np.linalg.norm(self.normalisation[listconfig]) ** 2
        M = M - Projnorm[:, :n - 1]
        #M = M - 1. / n

        PPinv = np.linalg.inv(np.dot(np.dot(M.T, P), M))
        D = np.dot(np.dot(M, PPinv), M.T)
        v = np.dot(D, trueprod[listconfig] - y[listconfig])

        g = np.zeros((2 * self.n_powerplant,))
        # The first are the dynamic costs, the last are the static ones.
        g[:self.n_powerplant][listconfig] = y[listconfig] * v
        g[self.n_powerplant:][listconfig] = v

        return g

    def grad_staticdynamiccosts(self, trueprod):
        """
        Compute the gradient of static and dynamic costs for a true production
        trueprod
        """
        trueconfig = get_power_on(trueprod, self.k_min, self.k_max)

        # FORMER VERSION
        """
        possible_config = [self.alwayson | ss
                           for ss in all_subsets(set(range(self.n_powerplant)) - self.alwayson)]

        # Keep only config such that productions is possible
        
        
        possible_config = [config for config in possible_config if
                           sum(self.k_max[i] * self.normalisation[i] for i in config) >= self._askedconf(config)]

        min_cost = np.inf
        min_sol = None

        for config in possible_config:
            y, cost = self.minimize_costs_config(config)
            cost += self.cost_config(config)

            if cost < min_cost:
                min_config = config
                min_cost = cost
                min_sol = y
        
        
        # store minimal config and use it and min_sol for interiorconfig computation
        # interiorconfig = config - set(np.where(np.logical_or(y == self.k_max, y == self.k_min))[0])
        interiorconfig = min_config - set(np.where(np.logical_or(min_sol == self.k_max, min_sol == self.k_min))[0])
        """
        y, cost = self.minimize_costs_oracle(trueprod)
        interiorconfig = trueconfig - set(np.where(np.logical_or(y == self.k_max, y == self.k_min))[0])
        return self._grad_interiorconfig(y, interiorconfig, trueprod)


def get_power_on(prod, k_min, k_max):
    return set(i for i in range(k_min.shape[0])
               if (prod[i] - k_min[i]) / (k_max[i] - k_min[i]) > threshold[i])


class SequencePrediction():

    def __init__(self, n_powerplant):
        self.n_powerplant = n_powerplant

    def predict(self, predmode, K_max, K_min, asked, seq, static_costs,
                dyn_costs, startup_costs, poweroff_costs, const_costs):
        """
        Main function for true prediction
        predmode can eather be : 
            * "seq" if the past is the true prediction in the sequence
              BEWARE, this is not the mode used in real life situation
            * "pred" if the past is the last predicted value. 
               This is the real-life situation
               In this mode, multiprocessing cannot be used (obviously)
        """
        n_steps, n_powerplant = np.shape(K_max)
        past = seq[0, :]
        pred_seq = np.zeros((n_steps, n_powerplant))

        normalisation = np.linalg.norm(seq, axis=0)
        seq = seq / normalisation
        K_max = K_max / normalisation
        K_min = K_min / normalisation
        static_costs = static_costs * normalisation
        dyn_costs = dyn_costs * normalisation ** 2

        pred_seq[0, :] = seq[0, :]

        if predmode == "seq":
            timesteppredlist = []
            for k in range(1, n_steps):
                power_on = get_power_on(past, K_min[k - 1, :], K_max[k - 1, :])
                timesteppred = TimeStepPrediction(static_costs, dyn_costs,
                                                  startup_costs, poweroff_costs, const_costs, past,
                                                  power_on, asked[k], K_min[k, :], K_max[k, :],
                                                  normalisation)
                timesteppredlist.append(timesteppred)

                past = seq[k, :]

            if npool > 1:
                with multiprocessing.Pool(npool) as p:
                    pred_list = p.map(_fun2, timesteppredlist)
            else:
                pred_list = map(_fun2, timesteppredlist)

            pred_seq[1:] = np.vstack(pred_list)

        elif predmode == "oracle":
            timesteppredlist = []
            targetlist = []
            for k in range(1, n_steps):
                power_on = get_power_on(past, K_min[k - 1, :], K_max[k - 1, :])
                #trueconfig = get_power_on(seq[k,:], K_min[k,:], K_max[k,:])
                targetlist.append(seq[k, :])
                timesteppred = TimeStepPrediction(static_costs, dyn_costs,
                                                  startup_costs, poweroff_costs, const_costs, past,
                                                  power_on, asked[k], K_min[k, :], K_max[k, :],
                                                  normalisation)
                timesteppredlist.append(timesteppred)

                past = seq[k, :]

            if npool > 1:
                with multiprocessing.Pool(npool) as p:
                    pred_list = p.map(_fun4, list(zip(timesteppredlist, targetlist)))
            else:
                pred_list = map(_fun4, list(zip(timesteppredlist, targetlist)))

            pred_seq[1:] = np.vstack(pred_list)

        elif predmode == "pred":
            for k in range(1, n_steps):
                if k % 100 == 0:
                    print(k)

                power_on = get_power_on(past, K_min[k - 1, :], K_max[k - 1, :])

                timesteppred = TimeStepPrediction(static_costs,
                                                  dyn_costs, startup_costs, poweroff_costs, const_costs,
                                                  past, power_on, asked[k], K_min[k, :], K_max[k, :], normalisation)
                pred_step, _ = timesteppred.minimize_costs()

                pred_seq[k, :] = pred_step
                past = pred_seq[k, :]
        else:
            raise ValueError("Unknown predmode :" + predmode + ". The only predmode are pred, seq and oracle")

        pred_seq = normalisation * pred_seq

        return pred_seq

    def fit_switchcosts(self, K_max, K_min, asked, seq, static_costs,
                        dyn_costs, startup_costs0, poweroff_costs0,
                        const_costs0):
        n_steps, n_powerplant = np.shape(K_max)

        normalisation = np.linalg.norm(seq, axis=0)
        seq = seq / normalisation
        K_max = K_max / normalisation
        K_min = K_min / normalisation
        static_costs = static_costs * normalisation
        dyn_costs = dyn_costs * normalisation ** 2

        past = seq[0, :]
        pred_seq = np.zeros((n_steps, n_powerplant))
        pred_seq[0, :] = seq[0, :]
        timesteplist = []
        for k in range(1, n_steps):

            power_on = get_power_on(past, K_min[k - 1, :], K_max[k - 1, :])
            timesteppred = TimeStepPrediction(static_costs, dyn_costs,
                                              startup_costs0, poweroff_costs0, const_costs0, past,
                                              power_on, asked[k], K_min[k, :], K_max[k, :], normalisation)

            timesteplist.append((timesteppred, seq[k, :]))
            past = seq[k, :]

        if npool > 1:
            with multiprocessing.Pool(npool) as p:
                conslist = p.map(_fun3, timesteplist)
        else:
            conslist = map(_fun3, timesteplist)

        #Gonlist = [Gon for Gon, Goff, Gactive, h in conslist]
        #Gofflist = [Goff for Gon, Goff, Gactive, h in conslist]
        #Gactivelist = [Gactive for Gon, Goff, Gactive, h in conslist]

        #Gonseq = np.vstack(Gonlist)
        #Goffseq = np.vstack(Gofflist)
        #Gactiveseq = np.vstack(Gactivelist)
        #h = np.concatenate(hlist)

        Glist = [np.hstack([gon, goff, gact]) for gon, goff, gact, h in conslist]
        hlist = [h for Gon, Goff, Gactive, h in conslist]

        x0 = np.concatenate([startup_costs0, poweroff_costs0, const_costs0])
        x = minimizeIntersectionPolytopes(Glist, hlist, x0, verbose=1)

        startup_costs = x[:self.n_powerplant]
        poweroff_costs = x[self.n_powerplant:2 * self.n_powerplant]
        const_costs = x[2 * self.n_powerplant:]
        return startup_costs, poweroff_costs, const_costs

    def grad_staticdynamiccosts(self, K_max, K_min, asked, seq,
                                static_costs, dyn_costs, startup_costs, poweroff_costs,
                                const_costs, normalisation):
        n_steps, n_powerplant = np.shape(K_max)

        past = seq[0, :]
        pred_seq = np.zeros((n_steps, n_powerplant))

        pred_seq[0, :] = seq[0, :]
        Gradlist = []

        timesteplist = []

        for k in range(1, n_steps):
            power_on = get_power_on(past, K_min[k - 1, :], K_max[k - 1, :])
            timesteppred = TimeStepPrediction(static_costs, dyn_costs,
                                              startup_costs, poweroff_costs, const_costs, past,
                                              power_on, asked[k], K_min[k, :], K_max[k, :],
                                              normalisation)
            timesteplist.append(timesteppred)
            past = seq[k, :]

        if npool > 1:
            with multiprocessing.Pool(npool) as p:
                Gradlist = p.map(_fun, list(zip(timesteplist, seq[1:])))
        else:
            Gradlist = map(_fun, list(zip(timesteplist, seq[1:])))

        G = np.vstack(Gradlist)
        return G.mean(axis=0)

    def fit_staticdynamiccosts(self, K_max, K_min, asked, seq,
                               static_costs0, dyn_costs0, startup_costs,
                               poweroff_costs, const_costs, steps=100,
                               verbose=0):

        normalisation = np.linalg.norm(seq, axis=0)
        seq = seq / normalisation
        K_max = K_max / normalisation
        K_min = K_min / normalisation
        static_costs0 = static_costs0 * normalisation
        dyn_costs0 = dyn_costs0 * normalisation ** 2

        # def evaluate(u):
        #    dyn_costs = u[:self.n_powerplant]
        #    static_costs = u[self.n_powerplant:]
        #    pred = self.predict_multiprocessing(K_max, K_min, asked, seq, static_costs, dyn_costs, startup_costs, poweroff_costs)
        #    evaluation = np.linalg.norm(pred - seq) ** 2
        #    #print("EVALUATION : ", evaluation)
        #    return evaluation

        def grad(u):
            dyn_costs = u[:self.n_powerplant]
            static_costs = u[self.n_powerplant:]
            g = self.grad_staticdynamiccosts(K_max, K_min, asked, seq,
                                             static_costs, dyn_costs, startup_costs, poweroff_costs,
                                             const_costs, normalisation)
            return g

        u0 = np.zeros((2 * self.n_powerplant))
        u0[:self.n_powerplant] = dyn_costs0
        u0[self.n_powerplant:] = static_costs0

        lr = 100.
        u = u0

        conditioning = np.zeros((2 * self.n_powerplant))
        conditioning[:self.n_powerplant] = normalisation ** 2
        conditioning[self.n_powerplant:] = normalisation
        # pdb.set_trace()
        for _ in range(steps):
            g = grad(u)
            gconditioned = g * conditioning
            u -= lr * grad(u)
            # print("Dyn costs:{.2f}\tStat costs:{.2f}".format( \
            #    u[:self.n_powerplant],u[self.n_powerplant:]))
            # if verbose == 1:
            #    metric = self.evaluate("oracle", K_max, K_min, asked, seq,
            #        u[self.n_powerplant:], u[:self.n_powerplant],
            #        startup_costs, poweroff_costs, const_costs)
            #    print(metric, u)

        dyn_costs = u[:self.n_powerplant]
        static_costs = u[self.n_powerplant:]

        dyn_costs = dyn_costs / normalisation**2
        static_costs = static_costs / normalisation
        return dyn_costs, static_costs

    def evaluate(self, predmode, K_max, K_min, asked, seq, static_costs,
                 dyn_costs, startup_costs, poweroff_costs, const_costs):

        pred = self.predict(predmode, K_max, K_min, asked, seq,
                            static_costs, dyn_costs, startup_costs, poweroff_costs, const_costs)
        # pdb.set_trace()

        countmax = (pred == K_max).sum(axis=0)
        countmin = (pred == K_min).sum(axis=0)
        print("countmin: {}\tcountmax: {}".format(countmin, countmax))
        normalisation = np.linalg.norm(seq, axis=0)
        prednorm = pred / normalisation
        seqnorm = seq / normalisation
        metric = np.linalg.norm(prednorm - seqnorm) ** 2
        return metric

    def fit(self, K_max, K_min, asked, seq, static_costs0, dyn_costs0,
            startup_costs0, poweroff_costs0, const_costs0):

        static_costs = static_costs0
        dyn_costs = dyn_costs0
        startup_costs = startup_costs0
        poweroff_costs = poweroff_costs0
        const_costs = const_costs0

        for _ in range(10000):

            metric = self.evaluate("oracle", K_max, K_min, asked, seq,
                                   static_costs, dyn_costs, startup_costs, poweroff_costs,
                                   const_costs)
            print("Startup costs : ", startup_costs)
            print("Poweroff costs", poweroff_costs)
            print("Dynamic costs", dyn_costs)
            print("Static costs", static_costs)
            print("Constant costs", const_costs)
            print("Metric : ", metric)
            print("\n")

            """
            newstartup_costs, newpoweroff_costs, newconst_costs = \
                self.fit_switchcosts(K_max, K_min, asked, seq, 
                    static_costs, dyn_costs, startup_costs, 
                    poweroff_costs, const_costs)

            # pred = self.predict_multiprocessing( \
            #    K_max, K_min, asked, seq, static_costs, dyn_costs,
            #    startup_costs, poweroff_costs)

            newmetric = self.evaluate("seq", K_max, K_min, asked, seq, 
                static_costs, dyn_costs, newstartup_costs, 
                newpoweroff_costs, newconst_costs)

            if newmetric < metric:
                print("New startup costs improved metric : ", newmetric, " < ", metric)
                startup_costs = newstartup_costs
                poweroff_costs = newpoweroff_costs
                const_costs = newconst_costs
            else:
                print("New startup costs did not improve : ", newmetric, " > ", metric)

            print("------------------------\n")
            """
            dyn_costs, static_costs = self.fit_staticdynamiccosts(
                K_max, K_min, asked, seq, static_costs, dyn_costs,
                startup_costs, poweroff_costs, const_costs,
                steps=5, verbose=0)

        return startup_costs, poweroff_costs, const_costs, dyn_costs, static_costs
