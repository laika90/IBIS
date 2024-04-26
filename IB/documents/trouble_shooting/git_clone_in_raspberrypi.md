# Raspberrypiにcloneしたい

## WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED! 

<症状>  

```zsh
$ ssh pi@raaspberrypi.local

@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@    WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!     @
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
IT IS POSSIBLE THAT SOMEONE IS DOING SOMETHING NASTY!
...
```

というように怒られらた場合。  

<原因>  

DHCPによってラズパイのIPアドレスが変わったのが原因。らしい。DHCPはIPIPアドレスを機器に割り振るシステムの名前のことみたい。  
過去の記録と比較して，前にアクセスしたホストと違うことにキレてるぽい。

<解決方法>
```zsh
$ ssh-keygen -R raspberrypi.local
```
で`pi@raspberrypi.local`のIPアドレスのホスト情報を削除。  

その後は普通に，
```zsh
ssh pi@raspberrypi.local 
```
で接続できる。 

## git clone で　fatal: Authentication failed for URL

<症状>  

```zsh
$ git clone <URL>

...
fatal: Authentication failed for <URL>
```
が出てきた。

<原因>  

`git clone`したら，usernameとpasswordの入力を求められるが，そのときに入力するパスワードが違う。  
このときに求められているパスワードは，githubアカウントのログインの際のパスワードではなく，PAT(personal access token)である。  

<解決方法>  

PATを作成してパスワード入力の際にペースト。  

PATの作成方法は，自分のgithubアカウントのsettings → Developer settings → personal access token に移動後，generate new を選択。  
Note は適当な説明。for b2multiとかでいい。  
repo の欄にチェックをつけて，tokenを作成。  

