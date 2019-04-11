import numpy as np


def div0(a, b, replacement=0):
    """ ignore / 0, div0( [-1, 0, 1], 0 ) -> [replacement, replacement, replacement] """
    with np.errstate(divide='ignore', invalid='ignore'):
        c = np.true_divide(a, b)
        try:
            c[~ np.isfinite(c)] = replacement * a[~ np.isfinite(c)]  # -inf inf NaN
        except TypeError:
            c[~ np.isfinite(c)] = replacement
    return c


def join_struct_arrays(arrays):
    sizes = np.array([a.itemsize for a in arrays])
    offsets = np.r_[0, sizes.cumsum()]
    n = len(arrays[0])
    joint = np.empty((n, offsets[-1]), dtype=np.uint8)
    for a, size, offset in zip(arrays, sizes, offsets):
        joint[:, offset:offset + size] = a.view(np.uint8).reshape(n, size)
    dtype = sum((a.dtype.descr for a in arrays), [])
    return joint.ravel().view(dtype)


def rollingMax(a, window):
    def eachValue():
        w = a[:window].copy()
        m = w.max()
        yield m
        i = 0
        j = window
        while j < len(a):
            oldValue = w[i]
            newValue = w[i] = a[j]
            if newValue > m:
                m = newValue
            elif oldValue == m:
                m = w.max()
            yield m
            i = (i + 1) % window
            j += 1
    temp = np.array(list(eachValue()))
    tuplepad = (int((window - 1) / 2), (window - 1) - int((window - 1) / 2))
    return np.lib.pad(temp, tuplepad, 'constant', constant_values=(temp[0], temp[-1]))


def rollingMin(a, window):
    def eachValue():
        w = a[:window].copy()
        m = w.min()
        yield m
        i = 0
        j = window
        while j < len(a):
            oldValue = w[i]
            newValue = w[i] = a[j]
            if newValue < m:
                m = newValue
            elif oldValue == m:
                m = w.min()
            yield m
            i = (i + 1) % window
            j += 1
    temp = np.array(list(eachValue()))
    tuplepad = (int((window - 1) / 2), (window - 1) - int((window - 1) / 2))
    return np.lib.pad(temp, tuplepad, 'constant', constant_values=(temp[0], temp[-1]))


def rollingMean(a, window):
    temp = np.convolve(a, np.ones((window,)) / window, mode='valid')
    tuplepad = (int((window - 1) / 2), (window - 1) - int((window - 1) / 2))
    return np.lib.pad(temp, tuplepad, 'constant', constant_values=(temp[0], temp[-1]))
