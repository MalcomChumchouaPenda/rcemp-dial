
import os
import sys

ROOT_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(ROOT_DIR, 'data')
SCRIPT_DIR = os.path.join(ROOT_DIR, 'scripts')
if SCRIPT_DIR not in sys.path:
    sys.path.append(SCRIPT_DIR)
