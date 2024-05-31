# IBIS
このmdファイルに各ディレクトリの情報をまとめてもらえると嬉しいです。
見てほしいpyファイル、担当名の順に書いているので自分の担当になってるところを書いてます(白倉)
優先順位はLibrary→unit_testの順でコメントとリドミ編集してもらえると助かります

書き方は
[ファイル名](担当名)
：ファイルの軽い説明  
となるようにお願いします。

(例)
LED_test(白倉)
:ラズパイのLチカ用のコード


制御の担当分野について 
収納・放出判定：　白坂、白倉、(原島)  
落下・着地判定：　田村、熊谷　(原島、杉本)  
飛行開始指示：　　熊谷　白倉  
飛行(一旦保留)  
画像航法　白倉　白坂　(栗田)  
↑これを元に確認してほしいところを振り分けてます。  


## `Library`
camera.py(白倉)
light.py(白坂)
logger_lib.py(田村)
lora.py(熊谷)
pixhawk.py(田村&白坂)←これだけめっちゃ多いので半分ずつ終わりそうになかったら白倉も手伝います



## `unit_test`
 ・action_test  
arm_test.py  
arm_without_gps.py  
arm_without_gps_with_log.py  
judge_takeoff.py  
lund_judge.py  
lund_judge_with_position.py  
image_navigation.py  
logger.py  
motor_test.py  
stored_judge.py  
takeoff_and_hovering.py  
takeoff_and_land.py  

・library_test  
fusefase.py  

・log_test  
logger.py  
mapping.py  


## `document`




## `Performance`


## `config`


## `loginibis.sh`
