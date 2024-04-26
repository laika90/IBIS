import os
import sys
import picamera
import cv2
import numpy as np
import datetime
from logger_lib import logger_info


class Camera:

    def __init__(self,
                 hsv_min_1 = np.array([0, 0, 0]),
                 hsv_max_1 = np.array([5,255,255]),
                 hsv_min_2 = np.array([150,0,0]),
                 hsv_max_2 = np.array([180,255,255]),
                 pixel_number_x = 2592,
                 pixel_number_y = 1944,
                 pixel_size = 1.4,
                 focal_length = 3.6):

        self.camera = picamera.PiCamera()
        self.hsv_min_1 = hsv_min_1
        self.hsv_max_1 = hsv_max_1
        self.hsv_min_2 = hsv_min_2
        self.hsv_max_2 = hsv_max_2
        self.pixel_number_x = pixel_number_x
        self.pixel_number_y = pixel_number_y
        self.pixel_size = pixel_size
        self.focal_length = focal_length

        self.image_path = None
        self.img  = None
        self.center_px = None
        self.image_length = None
        self.image_width = None
        self.res = None

        logger_info.info("Camera initialized")


    def take_pic(self):
        self.image_path = "/home/pi/ARLISS_IBIS/IB/Images/" \
                    + str(os.path.splitext(os.path.basename(sys.argv[0]))[0]) \
                    + "_" \
                    + str(datetime.datetime.now()) \
                    + ".jpg"
        logger_info.info("taking pic...: {}".format(self.image_path))
        self.camera.capture(self.image_path)


    def save_detected_img(self):

        cv2.circle(self.img, (int(self.center_px[0]), int(self.center_px[1])), 30, (0, 200, 0),
                    thickness=3, lineType=cv2.LINE_AA)
        cv2.imwrite(self.image_path, self.img)


    def detect_center(self):

        self.img = cv2.imread(self.image_path) # 画像を読み込む
        
        height, width = self.img.shape[:2] # 画像のサイズを取得する

        hsv = cv2.cvtColor(self.img, cv2.COLOR_BGR2HSV) # 色基準で2値化する

        # 色の範囲を指定する
        mask1 = cv2.inRange(hsv, self.hsv_min_1, self.hsv_max_1)

        # 赤色のHSVの値域2
        mask2 = cv2.inRange(hsv, self.hsv_min_2, self.hsv_max_2)

        mask = mask1 + mask2

        # 非ゼロのピクセルが連続してできた領域を検出する
        nlabels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask)

        #　画像の背景の番号は 0 とラベリングされているので、実際のオブジェクトの数は nlabels - 1 となる
        nlabels = nlabels - 1
        labels = np.delete(labels, obj=0, axis=0)
        stats = np.delete(stats, obj=0, axis=0)
        centroids = np.delete(centroids, obj=0, axis=0)
        centroids[:,0] = (width/2 - centroids[:,0]) / width*2
        centroids[:,1] = (height/2 - centroids[:,1]) / height*2
        percent = stats[:,4] / (height*width)
        
        self.res = {}

        if nlabels == 0:
            self.res['height'] = None
            self.res['width'] = None
            self.res['percent'] = 0
            self.res['center'] = None
            self.center_px = (0, 0)
            self.save_detected_img()
        else:
            max_index = np.argmax(percent)
            self.res['height'] = height
            self.res['width'] = width
            self.res['percent'] = percent[max_index]
            self.res['center'] = centroids[max_index]
            self.center_px = ((1-self.res['center'][0])*width/2, (1-self.res['center'][1])*height/2)
            self.save_detected_img()
        
        return self.res
    

    def get_target_position(self, distance):

        image_length = self.pixel_number_x * self.pixel_size / 1000
        image_width = self.pixel_number_y * self.pixel_size / 1000

        image_x = distance * image_length / self.focal_length
        image_y = distance * image_width / self.focal_length

        if not any(self.res['center'] == np.array([None, None])):
            x_m = self.res['center'][0]*image_x/2
            y_m = self.res['center'][1]*image_y/2

        else:
            x_m = None
            y_m = None

        return x_m, y_m

    def change_iso(self, iso_value):
        self.camera.iso = iso_value

    def change_shutter_speed(self, speed):
        self.camera.shutter_speed = speed


