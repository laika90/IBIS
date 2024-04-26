import asyncio
import os
import time
from datetime import datetime

import cv2


class LibcsRecord:
    def __init__(self, LOG_VIDEO_PATH):
        print("LibcsRecord initialized")
        self.is_taking = False
        self.path = LOG_VIDEO_PATH
        self.record_start_time = time.time()

    def start(self, fps=10, count=1):
        self.cap = cv2.VideoCapture(-1)
        self.w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))  # カメラの幅を取得
        self.h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))  # カメラの高さを取得
        self.fourcc = cv2.VideoWriter_fourcc("m", "p", "4", "v")  # 動画保存時の形式を設定
        self.fps = fps
        self.record_start_time = time.time()
        self.record_start_time_str = f"{datetime.now():%m%d_%H%M%S}"
        self.name = os.path.join(self.path, self.record_start_time_str + ".mp4")
        if count >= 2:
            self.name = os.path.join(
                self.path, self.record_start_time_str + "_" + str(count) + ".mp4"
            )
        self.is_taking = True
        self.video = cv2.VideoWriter(
            self.name, self.fourcc, self.fps, (self.w, self.h)
        )  # (保存名前、fourcc,fps,サイズ)
        print("recording start")

    def stop(self):
        print("recording stop")
        print("video saved as ", self.name)
        self.is_taking = False
        self.video.release()
        self.cap.release()
        cv2.destroyAllWindows()

    def update(self):
        self.read_start_time = time.time()
        ret, frame = self.cap.read()
        self.ret = ret
        self.frame = frame
        self.video.write(frame)  # 1フレーム保存する

    async def wait(self):
        elapsed_secs = time.time() - self.read_start_time
        if 1 / self.fps < elapsed_secs:
            await asyncio.sleep(0.01)
        else:
            await asyncio.sleep(1 / self.fps - elapsed_secs)

    async def cycle_record(self, pixhawk):
        pre_is_armed = pixhawk.armed
        fps = 10
        count = 0
        while True:
            if pre_is_armed != pixhawk.armed:
                if pixhawk.armed:
                    count = 1
                    self.start(fps, count)
                else:
                    self.stop()
            if (
                time.time() - self.record_start_time > 30
                and self.is_taking
                and pixhawk.armed
            ):
                count += 1
                self.stop()
                self.start(fps, count)
            if pixhawk.armed and self.is_taking:
                self.update()
                await self.wait()

            # if (not pixhawk.armed) and record.is_taking:
            #     record.stop()

            pre_is_armed = pixhawk.armed
            await asyncio.sleep(0.01)
