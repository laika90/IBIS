
import spidev #SPI通信のモジュール

#SPI通信のための準備
spi=spidev.SpiDev() #インスタンス生成
spi.open(0,0) #CE0（24番ピン）に接続したデバイスと通信を開始
spi.max_speed_hz=1000000 #転送速度を指定

#光センサのしきい値の設定
max_volume=0
#mode切り替え
print("maxモードならy、通常出力ならnを入力してください")
flag = str(input())
if flag == 'y':
    maxMode = True #trueで最大値出力
if flag == 'n':
    maxMode = False

#ループの中で値を読み込んで判定
if maxMode == True:
    while True:
        resp=spi.xfer2([0x68,0x00]) #SPI通信で値を読み込む
        volume=((resp[0]<<8)+resp[1])&0x3FF #値を10ビット数値に変換
        if volume > max_volume:
            max_volume = volume
            print(volume)
else:
    while True:
        resp=spi.xfer2([0x68,0x00])
        volume=((resp[0]<<8)+resp[1])&0x3FF
        print(volume)

