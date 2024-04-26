import sys
import os
sys.path.append(os.path.abspath("../humnavi"))
sys.path.append(os.path.abspath(".."))
from humnavi.pixhawk import Pixhawk

if __name__ == "__main__":
    pixhawk = Pixhawk()
    log_file = pixhawk.create_log_file()
    print(log_file)