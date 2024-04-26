import cv2

if __name__ == "__main__":
    cap = cv2.VideoCapture(0)
    frame_rate = 10 # フレームレート
    size = (640, 480) # 動画の画面サイズ

    fmt = cv2.VideoWriter_fourcc('m', 'p', '4', 'v') # ファイル形式(ここではmp4)
    writer = cv2.VideoWriter('./outtest.mp4', fmt, frame_rate, size) # ライター作成
    cap.set(21, 1.0)
    while True:
        ret, frame = cap.read()
        if ret:
            writer.write(frame) # 画像を1フレーム分として書き込み
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        else:
            print("no frame input")
            break
    cap.release()
    writer.release() # ファイルを閉じる
