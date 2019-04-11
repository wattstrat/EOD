
import threading

# config
config = None
configfile = None

# Global variable
redis = None
cache = None

calculs = None
loader = None
queue = None
jobs_calculs = None
sectorInCache = True
percentSimu = {}
lockPercentSimu = threading.Lock()
showProgressOnOptim = False
