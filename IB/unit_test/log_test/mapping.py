# あとで使うライブラリも併せて読み込み
import os
import folium
import pandas as pd
from time import sleep as slp
from selenium import webdriver
import glob
from selenium.webdriver.chrome.options import Options

# csvをpandas dataframeに保存
data = pd.read_csv("./gps.csv",encoding="shift_jis")

# 今回はA,Bの人しか居ないが、
# 一応何人来てもいいように人のリストを作り、
# それをforループで回す
person_list = data["人"].unique()

# 地図に表示する色
# foliumでサポートしているのは下記19色
color_list=['red','blue','green','purple','orange','darkred','lightred','beige','darkblue','darkgreen','cadetblue','darkpurple','white','pink','lightblue','lightgreen','gray','black','lightgray']

# 地図オブジェクトを作成
m = folium.Map(tiles='OpenStreetMap')

for idx,person in enumerate(person_list):
    # 一人分のデータだけをdata_tempに格納する
    data_temp = data[data["人"] == person]
    
    # data_tempの順番を日時で昇順ソート
    data_temp = data_temp.sort_values('日時', ascending=True)
    
    # data_tempの緯度経度だけを
    data_temp_lat_lon = data_temp[["緯度","経度"]]
    
    # 緯度経度を配列に格納
    locs = data_temp_lat_lon.values
    
    # 色を指定
    line_color = color_list[idx%len(color_list)]
    
    # 地図に線を追加する。緯度経度の配列をそのまま線として使う
    folium.PolyLine(locs,color=line_color,popup=person).add_to(m)
    
# 地図の表示範囲を緯度経度の最低最大とする
m.fit_bounds([[data["緯度"].min(),data["経度"].min()], [data["緯度"].max(),data["経度"].max()]])

# 地図を表示する
m