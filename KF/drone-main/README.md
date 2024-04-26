# drone
MAVSDK-Pythonを用いて実際にドローンを動かすためのpythonコードが入っているディレクトリ<br>
examplesフォルダ、nowusingフォルダ、loraフォルダに分かれます<br>
命名ふざけすぎてわかりにくくてすいません<br>
このディレクトリにあるコードに関しては、わからないところあれば生越まで聞いてください！

- examples
  - 一番最初良く分かっていないうちに、色々試したコードがあるフォルダ。px4公式が出しているサンプルコードをコピペしながら試行錯誤した形跡。
- nowusing
  - 松戸の試験飛行が本格化し始めた時に、exampleのもろもろと分けるために作ったフォルダ。本番に動かしたコードもこの中。
- lora
  - loraを色々試すために作ったフォルダ
  
## example
- arm.py
  - armするだけのコード
- goto.py
  - gotoモードの公式サンプルコードを引っ張ってきたコード。座標チューリッヒ。
- goto_matsudo.py
  - gotoモードを松戸で試すためのコード。gotoモードはうまく行った記憶はない。
- honban.py
  - mission慣れてきた頃に本番はこんな感じかな、と作ったコード。実際の本番の流れの大枠はこれ。
- matsudo_hikari.py
  -あらかじめ決めた閾値を光センサが超えたらmissionを始めるコード 
- matsudo_hikari_hold.py
  - 上のコードに、holdモードが切れたらholdに入れ直す機能を試みたコード。
  - 多分試験中にうまくいかなくて該当の部分はコメントアウトされてる
- matsudo_hikari_shikiichi.py
  - matsudo_hikari.pyに、閾値をその場に合わせて設定する機能を試みたコード
- mission_hikari_arm.py
  - あらかじめ決められた閾値を光センサが超えたらarmするコード
- mission_matsudo_faraway.py
  - ただのmission。座標チューリッヒ。
- mission_matsudo_high.py
  - ただのmission。座標チューリッヒ。
- mission_matsudo_normal.py
  - ただのmission。座標チューリッヒ。
- mission_nichidai.py
  - 日大飛行試験用のただのmission。60時間RTA後初めてmissionがうまく行った感動のコード。
- mission_sonomama.py
  - 公式サンプルmissionそのまま。
- mission_to_Japan.py
  - 日本にいくただのmission
- takeoff.py
  - ただtakeoffするだけのコード
- takeoff_1.5m.py
  - 1.5m takeoffして降りるコード
- takeoff_3m.py
  - 1.5m takeoffして降りるコード
  - QGCではtakeoff_altitudeを1.5mは低過ぎて設定できなかったので工夫したコード
  - 並列処理を初めて勉強して、その実践？的なノリで書いた
  - 結局蚊帳の中でうまくはいってないけど、コード的には合ってるはず
  - 並列で他のスレッドで高度を常に観察して、1.5mになったらlandをさせている
  - 並列やったことない人は超簡単で良い勉強になるかも？
- takeoff_only.py
  - ただtakeoff 

## nowusing
- gps_csv.py
  - よくわからない
- gpssearch.py
  - その場のgpsを表示してくれるコード
  - 本番もアメリカで使った
  - これを走らせて、gpsを実際に動かすコードにコピペして、gpsの値を設定してた
- hold_fight.py
  - holdに実際に入るまでholdに入れ続けてくれるコード
  - 本番もアメリカで使った
- honban_fight_mukaikaze.py
  - 本番の向かい風用コード。実際は追い風だったので使ってはない。
- honban_fight_oikaze.py
  - 本番の追い風用コード。
  - コードは本番も完璧に動いた。
  - これが全て。
- hover.py
  - その場でhoverするコード
  - 電力消費試験するために作ったけどそんな使わなかった記憶
- kaya_hikari.py
  - 
- kaya_hikari_GPS.py
- kaya_hikari_hold.py
- kaya_hikari_shikiichi.py
- kill.py
- land.py
- matsudo2_hikari_shikiichi.py
- matsudo2_summer.py
- matsudo_hikari.py
- matsudo_lora_summer.py
- matsudo_toma_infinity.py
- preflightcheck.py
- read_hikari.py
## lora
