
import os
from uuid import uuid4
import queue as que
import logging as log
import functools as fct
from logging import handlers as logh


CUR_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CUR_DIR)
LOGS_DIR = os.path.join(ROOT_DIR, 'logs')

_LOG_BACKUP_COUNT = 100
_LOG_MAX_BYTES = 20000000
_LOG_DEFAULT_SEPARATOR = ' - '
_LOG_ATTRIBUTES_LIST = ['asctime', 'levelname', 'message'] 
_LOG_FORMAT = '%(' + ((')s' + _LOG_DEFAULT_SEPARATOR + '%(').join(_LOG_ATTRIBUTES_LIST)) + ')s'
_FORMATTER = log.Formatter(_LOG_FORMAT)
# _LOG_QUEUES = {}


def get_logger(name, verbose=None):
    level = log.DEBUG if verbose else log.WARNING
    log_uid = uuid4().hex
    logfile = os.path.join(LOGS_DIR, '%s_%s.log' % (name, log_uid))
    filehandler = logh.RotatingFileHandler(logfile, 
                                            maxBytes=_LOG_MAX_BYTES, 
                                            backupCount=_LOG_BACKUP_COUNT)
    filehandler.setFormatter(_FORMATTER)
    filehandler.setLevel(level)

    logger = log.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(filehandler)
    return logger


# def get_logger(name, verbose=None):
#     level = log.DEBUG if verbose else log.WARNING
#     if name in _LOG_QUEUES:
#         queuehandler = _LOG_QUEUES[name]
#     else:
#         log_uid = uuid4().hex
#         logqueue = que.Queue()
#         queuehandler = logh.QueueHandler(logqueue)
#         logfile = os.path.join(LOGS_DIR, '%s_%s.log' % (name, log_uid))
#         filehandler = logh.RotatingFileHandler(logfile, 
#                                                maxBytes=_LOG_MAX_BYTES, 
#                                                backupCount=_LOG_BACKUP_COUNT)
#         filehandler.setFormatter(_FORMATTER)
#         filehandler.setLevel(level)
#         listener = logh.QueueListener(logqueue, filehandler)

#     logger = log.getLogger(name)
#     logger.setLevel(level)
#     logger.addHandler(queuehandler)
#     logger.stop = listener.stop
#     listener.start()
#     return logger

