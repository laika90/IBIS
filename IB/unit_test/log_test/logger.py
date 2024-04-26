import sys
import os
import datetime

def create_logger_log_file():
    LOG_DIR = os.path.abspath("~/ARLISS_IBIS/log")
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    log_path = LOG_DIR + "/" + str(datetime.date.today())
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

    logger_info = getLogger("sub1") # loggerを生成
    logger_info.setLevel(INFO) 

    logger_debug = getLogger("sub2") # loggerを生成
    logger_debug.setLevel(DEBUG) 

    # Formatter
    handler_format = Formatter('%(asctime)s.%(msecs)-3d' +
                               ' [%(levelname)-4s]:' +
                               ' %(message)s',
                               datefmt='%Y-%m-%d %H:%M:%S') # 時間、レベル、メッセージ

    # stdout Hnadler
    sh = StreamHandler(sys.stdout) # stdout:標準出力
    sh.setLevel(INFO) #いらないかも
    sh.setFormatter(handler_format) #どのハンドラにくっつくかを指定

    # file Handler
    log_file = create_logger_log_file()
    print(log_file)

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
#
logger_info, logger_debug = set_logger()
