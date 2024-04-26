# ラズパイでのpushでパスワード聞かれる時の対処法

httpsになっていることが原因です。

まずはgithubのcodeから、sshでのリンクを取得します。
サーバー名は`origin`とします。

```bash
$ git remote set-url origin {コピーしたリンク貼り付け}
```

そしたら、sshの公開鍵設定をします。

```bash
$ ssh-keygen -t rsa
```

そしたら公開鍵を見にいきます。

```bash
$ cat ~/.ssh
```

これをコピーします。一番最初から全部コピーしてください。

githubに行って、設定からSSH公開鍵登録してください。

```bash
ssh -T git@github.com
```

ってやって、`Hi! うんちゃらかんちゃら！`みたいなのが出ればいいです。