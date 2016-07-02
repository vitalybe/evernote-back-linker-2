import logging
import logging.handlers
from os import path

LOG_FILE = path.join(path.dirname(__file__), "logs", "output.log")
LOG_LEVEL = logging.DEBUG

logging.root.setLevel(LOG_LEVEL)

# Output file
fh = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=100000, backupCount=1)
fh.setLevel(LOG_LEVEL)

# Console output
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# create formatter and add it to the handlers
formatter = logging.Formatter("%(message)s")
ch.setFormatter(formatter)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] [%(name)s] %(message)s", '%d/%b/%y %H:%M:%S')
fh.setFormatter(formatter)

# add the handlers to logging.root
logging.root.addHandler(ch)
logging.root.addHandler(fh)

logging.getLogger('sh.command').setLevel(logging.WARN)
logging.getLogger('sh.stream_bufferer').setLevel(logging.WARN)
logging.getLogger('sh.streamreader').setLevel(logging.WARN)

def getLogger(name):
    return logging.getLogger(name)