#encoding=utf-8

import logging
import os.path
import os
import sys

"""
日志使用方法：
from logger import log

log.info('your info')
log.debug('heyhey')

"""

LOG_ROOT = os.path.abspath(os.path.dirname(__file__))

# 日志格式设置
LOG_FILE = os.path.join(LOG_ROOT,'%s.log'%LOG_ROOT.split(os.path.sep)[-1:][0])  # 日志文件保存位置,默认与本文件同一个目录,并以目录名为日志文件名
LOG_LEVEL = logging.DEBUG # 日志的输出级别，有 NOTSET, DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT = '[%(asctime)s] %(funcName)s(%(filename)s:%(lineno)s) [%(levelname)s]:%(message)s' # 日志的输出格式
# 日志格式设置结束

def create_log():
    logger = logging.getLogger()
    formatter = logging.Formatter(LOG_FORMAT)
    filehandler = logging.FileHandler(LOG_FILE)
    filehandler.setFormatter(formatter)
    streamhandler = logging.StreamHandler()
    streamhandler.setFormatter(formatter)
    logger.setLevel(LOG_LEVEL)
    logger.addHandler(filehandler)
    logger.addHandler(streamhandler)
    return logger

log = create_log()

def log_exce(msg=None):
    if msg:
        log.error(msg)
        excinfo = sys.exc_info()
        log.error(excinfo[0])
        log.error(excinfo[1])
