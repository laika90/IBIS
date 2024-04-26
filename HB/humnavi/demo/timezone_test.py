import datetime

unix_epoch_time = 1660726810
tz_jst = datetime.timezone(datetime.timedelta(hours=9))
dt_jst = datetime.datetime.fromtimestamp(unix_epoch_time, tz_jst)
print("JST:", dt_jst)
tz_pdt = datetime.timezone(datetime.timedelta(hours=-7))
dt_pdt = datetime.datetime.fromtimestamp(unix_epoch_time, tz_pdt)
print("PDT:", dt_pdt)
