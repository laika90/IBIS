#8/30未実験
import datetime
import json

file_path = "/home/pi/ARLISS_IBIS/IB/config/matsudo_config/other_param_matsudo_condig.json"

with open(file_path, mode="r") as f:
    other_param = json.load(f)
print(json.dumps(other_param, indent=2))

#yesを押し続ければ複数パラメータ変更可能
is_continue_setting = True
while is_continue_setting:
    key_name = input("enter the key of the parameter you want to change: ")
    parameter = input("write down the parameters after the change: ")
    other_param[key_name] = parameter
    
    choice = input("do you want to continue? Please respond with 'yes' or 'no': ")
    if choice in ['y', 'ye', 'yes']:
        is_continue_setting = True
    elif choice in ['n', 'no']:
        is_continue_setting = False
   
#configの変更時刻を記録     
dt_now = datetime.datetime.now().isoformat()
other_param["set time"] = dt_now

with open(file_path, mode="w") as f:
    json.dump(other_param, f, indent=4)
    print("these are parameters after the change"+"\n"+json.dumps(other_param, indent=2))

print("all parameters have been updated")