import sys
import math
import threading

lockProgress = threading.Lock()


def printProgress(iteration, total, end=False, prefix='', suffix='', decimals=1, barLength=100, lock=False):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        barLength   - Optional  : character length of bar (Int)
    """
    if lock:
        lockProgress.acquire()
    if iteration > total:
        iteration = total
    formatStr = "{0:.%df}" % (decimals)
    percents = formatStr.format(100 * (iteration / float(total)))
    filledLength = int(round(barLength * iteration / float(total)))
    bar = '█' * filledLength + '-' * (barLength - filledLength)
    if math.floor(iteration) % math.floor(total / 100) == 0:
        sys.stdout.write('\r%s |%s| %s%s %s' % (prefix, bar, percents, '%', suffix)),
    if iteration >= total:
        sys.stdout.write('\r%s |%s| %s%s %s' % (prefix, bar, percents, '%', suffix)),
        if end:
            sys.stdout.write('\n')
    sys.stdout.flush()
    if lock:
        lockProgress.release()
