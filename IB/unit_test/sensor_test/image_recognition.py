import picamera
import cv2
import numpy as np
import time
import datetime

class Camera:
    
    def __init__(self):
        self.camera = picamera.PiCamera()
        print('キャメラ初期化完了')
    
    def take_pic(self, file_path):
        self.camera.capture(file_path)

    def save_detected_img(self, file_path, img, center_px):
        cv2.circle(img, (int(center_px[0]), int(center_px[1])), 30, (0, 200, 0),
                thickness=3, lineType=cv2.LINE_AA)
        cv2.imwrite(file_path, img)

    def detect_center(self, file_path):
        img = cv2.imread(file_path) # 画像を読み込む
        
        height, width = img.shape[:2] # 画像のサイズを取得する

        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV) # 色基準で2値化する

        # 色の範囲を指定する
        hsv_min = np.array([0,145,0])
        hsv_max = np.array([5,255,255])
        mask1 = cv2.inRange(hsv, hsv_min, hsv_max)

        # 赤色のHSVの値域2
        hsv_min = np.array([150,110,0]) #カメラ故障のため，0→150へ変更
        hsv_max = np.array([179,255,255])
        mask2 = cv2.inRange(hsv, hsv_min, hsv_max)

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
        
        res = {}
        if nlabels == 0:
            res['height'] = None
            res['width'] = None
            res['percent'] = 0
            res['center'] = None
        else:
            max_index = np.argmax(percent)
            res['height'] = height
            res['width'] = width
            res['percent'] = percent[max_index]
            res['center'] = centroids[max_index]
            self.save_detected_img(file_path, img, ((1-res['center'][0])*width/2, (1-res['center'][1])*height/2))
        
        return res


if __name__ == "__main__":
    camera = Camera()
    
    file_No = 0
    while True:
        file_path = '/home/pi/ARLISS_IBIS/IB/Images/image{:>03d}{}.jpg'.format(file_No, datetime.datetime.now())
        file_No += 1

        print("taking pic...: {}".format(file_path))
        camera.take_pic(file_path) # 写真を撮る
        res = camera.detect_center(file_path) # 赤の最大領域の占有率と重心を求める

        if res['percent'] < 0.005: # 赤の領域が少ない場合は、旋回する
            print('too little')
            continue

        if res['percent'] > 0.5: # 赤の領域が大きい場合は、終了する
            print('enough')
            break

        dif_arg = res['center'][0] * np.pi/6

        # ログの出力
        print('percent={}, center={}, dif_arg={}'.format(res['percent'], res['center'], dif_arg))
        
        time.sleep(1)

    cv2.destroyAllWindows()