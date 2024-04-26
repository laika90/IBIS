import sys
import os
import datetime

def create_logger_log_file():
    LOG_DIR = os.path.abspath("log")
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    log_path = LOG_DIR + "/" + str(datetime.date.today()) + "_logger"
    i = 0
    while True:
        log_file = log_path + "/" + str(i).zfill(3)
        if os.path.exists(log_file):
            print(log_file + " already exists")
            i += 1
            continue
        else:
            try:
                with open(log_file, mode="w"):
                    pass
            except FileNotFoundError:
                os.mkdir(log_path)
                with open(log_file, mode="w"):
                    pass
            return str(log_file)

def set_logger():
    from logging import (getLogger, StreamHandler, FileHandler, Formatter,
                         DEBUG, INFO, WARNING, ERROR)

    logger_info = getLogger("sub1")
    logger_info.setLevel(INFO)

    logger_debug = getLogger("sub2")
    logger_debug.setLevel(DEBUG)

    # Formatter
    handler_format = Formatter('%(asctime)s.%(msecs)-3d' +
                               ' [%(levelname)-4s]:' +
                               ' %(message)s',
                               datefmt='%Y-%m-%d %H:%M:%S')

    # stdout Hnadler
    sh = StreamHandler(sys.stdout)
    sh.setLevel(INFO)
    sh.setFormatter(handler_format)

    # file Handler
    log_file = create_logger_log_file()

    log =  FileHandler(log_file, 'a', encoding='utf-8')
    log.setLevel(INFO)
    log.setFormatter(handler_format)

    debug = FileHandler(log_file, 'a', encoding='utf-8')
    debug.setLevel(DEBUG)
    debug.setFormatter(handler_format)

    # add Handler
    logger_info.addHandler(sh)
    logger_info.addHandler(log)
    logger_debug.addHandler(debug)

    return logger_info, logger_debug

logger_info, logger_debug = set_logger()

logger_info.info("unauthorized.")
logger_debug.debug("unauthorized.")
