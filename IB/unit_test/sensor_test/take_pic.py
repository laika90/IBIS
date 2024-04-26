import picamera
import datetime



class Camera:
    
    def __init__(self):
        self.camera = picamera.PiCamera()
        print('キャメラ初期化完了')
    
    def take_pic(self, file_path):
        self.camera.capture(file_path)
        
    
if __name__ == "__main__":
    camera = Camera()
    
    file_path = '/home/pi/ARLISS_IBIS/IB/Images/image_test{}.jpg'.format(datetime.datetime.now())

    print("taking pic...: {}".format(file_path))
    camera.take_pic(file_path) # 写真を撮る