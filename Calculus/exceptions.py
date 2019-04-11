class CalculusError(Exception):
    def __init__(self, varname=None):
        self.varname = varname

    def __str__(self):
        return "CalculusError:"


class UnknownError(Exception):
    def __str__(self):
        return "UnknownError:"


class CalculusPostponed(Exception):
    def __init__(self, varname=None):
        self.varname = varname

    def __str__(self):
        return "CalculusPostponed:"


class CalculusDepend(CalculusPostponed):
    def __init__(self, var_missing):
        super().__init__()
        self.depend = var_missing

    def __str__(self):
        return "CalculusDepend:%s" % (self.depend)


class FunctionCalcNeeded(Exception):
    def __init__(self, fun, args):
        super().__init__()
        self._fun = fun
        self._args = args

    # function is callable => call function
    # function is a string => get calculus from CalculusInstance
    def _value_from_fun(self, CalculusInstance=None):
        if self._function is None:
            return None

        if isinstance(self._args, tuple) and len(self._args) == 2:
            args = self._args[0]
            kwargs = self._args[1]
        else:
            args = []
            kwargs = {}

        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}

        if callable(self._fun):
            value = self._fun(*args, **kwargs)
        elif isinstance(self._fun, str) and CalculusInstance is not None:
            calc = CalculusInstance.calculus(self._fun)
            value = calc(*args, **kwargs)
        else:
            return None

        return value

    def tryCalculation(self, CalculusInstance=None):
        return self.value_from_fun(CalculusInstance)
