import os
import sys
import mavsdk

import RPi.GPIO as GPIO
import serial

sys.path.append(os.getcwd())
import asyncio
import struct

class Lora:
    def __init__(self):
        # pin number
        # reset
        self.rst = 17
        # Vin
        self.power = 4

        # 改行文字
        self.CRLF = "\r\n"
        # massage received from PC on ground
        self.msg_received = "hello, world"

        # serial
        self.serial = serial.Serial("/dev/ttyS0", 115200, timeout=1)

        # power
        self.is_on = False
        # is out of carrier?
        self.is_out = False
        #         self.is_sending = False

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.rst, GPIO.OUT)
        GPIO.setup(self.power, GPIO.OUT)

    async def power_off(self) -> None:
        """cut power for lora"""
        GPIO.output(self.power, GPIO.LOW)
        self.is_on = False
        await asyncio.sleep(1)

    async def power_on(self):
        """start lora"""
        GPIO.output(self.power, GPIO.HIGH)

        GPIO.output(self.rst, GPIO.LOW)
        await asyncio.sleep(2)
        GPIO.output(self.rst, GPIO.HIGH)
        await asyncio.sleep(2)
        print("lora power on")
        await self.write("processor")
        await self.write("start")

        self.is_on = True

    async def write(self, massage: str) -> None:
        """write lora

        Args:
          massage (str): command or massage to send
        """
        #         self.is_sending = True
        msg_send = str(massage) + self.CRLF
        self.serial.write(msg_send.encode("ascii"))
        await asyncio.sleep(4)

    #         self.is_sending = False

    async def read(self) -> None:
        """clear header and read lora"""
        data = self.serial.readline()
        fmt = "4s4s4s" + str(len(data) - 14) + "sxx"  # rssi, rcvidが両方onの時のヘッダー除去

        try:
            line = struct.unpack(fmt, data)
            self.msg_received = line[3].decode("ascii")
            await asyncio.sleep(1)
        except struct.error:
            await asyncio.sleep(1)

    async def close(self) -> None:
        """close serial connection"""
        self.serial.close()

    async def check_gps(self, pixhawk) -> None:
        """check num_satellites and absolute_altitude_m and judge if drone is out of carrier"""
        if pixhawk.num_satellites > 6:
            if pixhawk.absolute_altitude_m > 2000:
                self.is_out = True
        await asyncio.sleep(1)

    async def switch_lora(self, pixhawk):
        """turn off lora until drone is out of carrier"""
        while True:
            await self.check_gps(pixhawk)
            if self.is_out:
                await self.power_on()
                return
            await self.power_off()

    async def cycle_send_position(self, pixhawk):
        while True:
            if self.is_on:
                lat = "lat" + str(pixhawk.latitude_deg)
                lng = "lng" + str(pixhawk.longitude_deg)
                alt = "alt" + str(pixhawk.absolute_altitude_m)
                await self.write(lat)
                await self.write(lng)
                await self.write(alt)
            await asyncio.sleep(10)  # this must be a little long because lora cannot receive message while sending

    async def cycle_receive_lora(self, pixhawk):
        while True:
            #             while True:
            #                 if not self.is_sending:
            #                     break;
            #                 await asyncio.sleep(0.01)
            await self.read()
            print("msg_received:", self.msg_received)
            if self.msg_received == "kill":
                try:
                    await pixhawk.kill()
                except mavsdk.action.ActionError:
                    self.msg_received = "hello, world"

            if self.msg_received == "land":
                try:
                    await pixhawk.land()
                except mavsdk.action.ActionError:
                    self.msg_received = "hello, world"
            await asyncio.sleep(1)


# async def main():
#     lora = Lora()
#     pixhawk = Pixhawk()
#     await lora.power_on()
#     main_coroutines = [ lora.cycle_receive_lora(pixhawk)]
#     await asyncio.gather(*main_coroutines)
#
#
# if __name__ == "__main__":
#      aiorun.run(main())
