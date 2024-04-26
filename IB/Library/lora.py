import RPi.GPIO as GPIO
import serial
import asyncio
from logger_lib import logger_info
import time
from mavsdk import System
import json


class Lora:
    
    def __init__(self,
                 lora_power_pin,
                 lora_sleep_time,
                 use_other_param_config = False):
        
        if use_other_param_config:
            json_pass_other_param = "/home/pi/ARLISS_IBIS/IB/config/matsudo_config/other_param_matsudo_config.json"
            f = open(json_pass_other_param , "r")
            other_param = json.load(f)
            self.lora_power_pin = float(other_param["lora_power_pin"])
            self.lora_sleep_time = float(other_param["lora_sleep_time"])
            f.close()
        else:
            self.lora_power_pin = lora_power_pin
            self.lora_sleep_time = lora_sleep_time
            
        self.pix = System()
        self.CRLF = "\r\n"
        self.is_lora_power_on = False
        self.connect_counter = 0
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.lora_power_pin, GPIO.OUT)
        
        logger_info.info("Lora initialized")
        
        
    def serial_connect(self):
    
        connect_counter = 0
        while True:
            try:
                self.serial = serial.Serial('/dev/ttyS0', 115200, timeout=0.6)
            except:
                logger_info.info ("Serial port error. Waiting.")
                connect_counter += 1
                if connect_counter >= 10:
                    break
                time.sleep(3)
            else:
                break
        logger_info.info("Serial port OK.")
        self.operation_write()
        self.serial.write(("Lora start\r\n").encode())
        logger_info.info("Lora READY")
    
        
    def operation_write(self):
        
        self.serial.write(b'2\r\n')
        time.sleep(1)
        self.serial.write(b'z\r\n')
        time.sleep(1)
        
       
    async def power_off(self):
        
        GPIO.output(self.lora_power_pin, GPIO.LOW)
        self.is_lora_power_on = False
        logger_info.info("Lora power off")
        await asyncio.sleep(1)
        

    async def power_on(self):
        
        GPIO.output(self.lora_power_pin, GPIO.HIGH)
        logger_info.info("Lora power on")
        self.serial_connect()

        self.is_lora_power_on = True
            
    
    async def write(self, message: str):
        
        msg_send = str(message) + self.CRLF
        self.serial.write(msg_send.encode("ascii"))
        await asyncio.sleep(self.lora_sleep_time)