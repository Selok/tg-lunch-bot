import os
import sys

import logging
import logging.config

ENROLL_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    'enroll'
))

logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(module)s - %(funcName)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

def setup():
    if not os.path.isdir(ENROLL_DIR):
        os.mkdir(ENROLL_DIR)

        
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    root.addHandler(handler)
