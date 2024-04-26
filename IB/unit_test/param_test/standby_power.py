import datetime
import time

while True:
    time_now = datetime.datetime.now().time()
    print(time_now)
    time.sleep(30)
    