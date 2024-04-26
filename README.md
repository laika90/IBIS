# IBIS

ちなみにRaspberrypiへのログインパスワードは大体`ibis`です。  
無理だったら`cansat`で多分入れます。

## ディレクトリ構成

`HB`, `KF`, `IB`の3つがあります。  
`HB`はHumming Bird、`KF`はKing Fisher、`IB`はIbisのディレクトリです。  
なんだかんだ見やすいので先輩方のディレクトリをそのまま入れていました。

## `Library`
各クラスをここにまとめていました。  
大体各系ごとにクラスを書いていました。  
多分中身見ればわかると思います。

## `unit_test`
 
本番コードやEnd to Endのような一連のシーケンスではなく、個別のユニットテストを行なったファイルを集めたディレクトリです。  
* `action_test` : pixhawkを用いた飛行
* `library_test` : 作成したライブラリの確認
* `log_test` : logの出力テスト
* `lora_test` : ローラ (通信) のテスト
* `param_test` : pixhawkなどのパラメータテスト
* `sensor_test` : センサー関連のテスト

## `document`
トラブルシューティングとか書いてました。

## `Performance`
だいたい本番用のコードです。
* `ARLISS.py` : 本番用コード
* `MTD.py` : 松戸用テストコード
* `NSE.py` : 能代宇宙イベント本番用コード
* `gps_ave.py` : 能代宇宙イベント本番用のGPS座標を取るためのコード．ARLISS本番はガーミン(砂漠で遭難しないためのGPS)を使用．
* `logger_performance.py` : 本番用のlogger

* `timer_MTD.txt`, `timer_NSE.txt`, `timer_debag.txt` : timer関係のパラメータ

## `config`
コードは書いたけど実際に使ったことはないです．  
想定する使い方としては2種類のjsonファイルを飛行させるためのファイルに読み込ませて実行させます。  
* `GPS_matsudo_config.json`の中身をpythonファイルを実行することで書き換えさせます
* `other_param_matsudo_config.json`はその都度手動設定

## `loginibis.sh`
ラズパイにssh接続するのを自動でやってくれるシェルスクリプトです。  
適当にラズパイの名前とパスワードを変えて使ってもらったら良いと思います。