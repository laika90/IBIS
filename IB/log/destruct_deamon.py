def destruct_deamon():
    while True:
        print("How do you destruct deamon?")
        print("Type\n 1:PC 2:raspberrypi")
        destruct_way = input()
        if destruct_way == "1":
            print("Please try it on \"ARLISS_IBIS\"")
            deamon_log_pass = "IB/log/Performance_log.txt"
            deamon_error_pass = "IB/log/Performance_error.txt"
        elif destruct_way == "2":
            deamon_log_pass = "/home/pi/ARLISS_IBIS/IB/log/Performance_log.txt"
            deamon_error_pass = "/home/pi/ARLISS_IBIS/IB/log/Performance_error.txt"
        else:
            print("Something wrong. Try again")
            continue
        try:
            deamon_log = open(deamon_log_pass, "w")
            deamon_error = open(deamon_error_pass, "w")
        except FileNotFoundError:
            print("Please try it again on \"ARLISS_IBIS\"")
            return
        deamon_log.write("")
        deamon_error.write("")
        print("Destructed")
        break

destruct_deamon()