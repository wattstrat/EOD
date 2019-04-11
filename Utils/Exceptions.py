class Exceptions(Exception):
    def __init__(self, message, *args):
        super().__init__(message)
        self._e = args

    def __str__(self):
        return "Exceptions: [%s]" % (','.join(['%s' % str(ex) for ex in self._e]))

    def __repr__(self):
        return "Exceptions: [%s]" % (','.join(['%s' % repr(ex) for ex in self._e]))


class KeyErrorExceptions(KeyError):
    def __init__(self, message, *args):
        super().__init__(message)
        self._e = args

    def __str__(self):
        return "Multiple KeyError: [%s]" % (','.join(['%s' % str(ex) for ex in self._e]))

    def __repr__(self):
        return "Multiple KeyError: [%s]" % (','.join(['%s' % repr(ex) for ex in self._e]))
