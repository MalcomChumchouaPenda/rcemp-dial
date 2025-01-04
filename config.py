
import os
import sys

ROOT_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(ROOT_DIR, 'data')
SCRIPT_DIR = os.path.join(ROOT_DIR, 'scripts')
LOG_DIR = os.path.join(DATA_DIR, 'logs')
if not os.path.isdir(LOG_DIR):
    os.makedirs(LOG_DIR)
    
RESULT_DIR = os.path.join(DATA_DIR, 'results')
MYSQL_USERNAME = 'demo'
MYSQL_USERPWD = 'demo'
DEFAULT_SEED = 0

