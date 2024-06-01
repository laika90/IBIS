import sys
import os
import datetime

#log fileの作成
def create_logger_log_file():
    LOG_DIR = "/home/pi/ARLISS_IBIS/IB/log" #KF,HBなどのファイルを使わず、IBのみ使うなら/home/pi/IB/logでよさそう
    if not os.path.exists(LOG_DIR): 
        os.makedirs(LOG_DIR) 
    log_path = LOG_DIR + "/" + str(datetime.date.today()) #log内のファイル参照
    i = 0
    while True:
        file_name = str(i).zfill(3) + "_" + str(os.path.splitext(os.path.basename(sys.argv[0]))[0]) #sample.py内で使った場合、ファイル名は 001_sampleのようになる
        log_file = log_path + "/" + file_name
        try:
            is_dir_exist = any(file for file in os.listdir(log_path)) #指定directoryが存在するかどうかのbool
            pass
        except FileNotFoundError: #log_pathがまだできていないなら作る
            os.mkdir(log_path)
            pass
        if any(file.startswith(file_name[:3]) for file in os.listdir(log_path)): #001が存在するなら002にする
            print(str(i).zfill(3) + " already exists")
            i += 1
            continue
        else:
            with open(log_file, mode="w"): #書き込みモードでファイルを開く
                pass
            return str(log_file)

#loggerの設定
def set_logger():
    from logging import (getLogger, StreamHandler, FileHandler, Formatter,
                         DEBUG, INFO, WARNING, ERROR)

    logger_info = getLogger("sub1") # loggerを生成
    logger_info.setLevel(INFO) #リンク集のloggerのレベルについてのサイト参照

    logger_debug = getLogger("sub2") # loggerを生成
    logger_debug.setLevel(DEBUG) #リンク集のloggerのレベルについてのサイト参照

    # Formatter:ログの表示形式を設定
    handler_format = Formatter('%(asctime)s.%(msecs)-3d' +
                               ' [%(levelname)-4s]:' +
                               ' %(message)s',
                               datefmt='%Y-%m-%d %H:%M:%S') # 時間、レベル、メッセージ

    # stdout Handler
    sh = StreamHandler(sys.stdout) # stdout:標準出力
    sh.setLevel(INFO) #いらないかも
    sh.setFormatter(handler_format) #どのハンドラにくっつくかを指定

    # file Handler
    log_file = create_logger_log_file()

    log =  FileHandler(log_file, 'a', encoding='utf-8') #mode = 'a'の場合はファイルに追記していく。'w'の場合はコード実行のたびに新しいファイルを用意する
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
#実行
logger_info, logger_debug = set_logger()