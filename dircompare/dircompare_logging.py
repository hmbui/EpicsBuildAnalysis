import os
import logging

try:
    os.makedirs("logs")
except os.error as err:
    # It's OK if the log directory exists. This is to be compatible with Python 2.7
    if err.errno != os.errno.EEXIST:
        raise err

logging.basicConfig(level=logging.INFO, filename="logs/dircompare.log",
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Override the basic configs for cleaner console output
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(logging.Formatter("%(message)s"))
logger = logging.getLogger('').addHandler(console_handler)
