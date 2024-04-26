# 03 Git Quick Reference

コマンド集です。

## status

普通の。statusを表示
```
$ git status
```

簡易バージョン
```
$ git status -s
$ git status --short
```

## add

add
```
$ git add {ファイル名1} {ファイル名2} ...
```

## commit 

簡易メッセージ付きコミット
```
$ git commit -m "メッセージ"
```

ステージングエリアの省略。簡易メッセージ付き（ add + commit -m ）
```
$ git commit -a -m "メッセージ"
```

## rm

削除
```
$ git rm {ファイル名1} {ファイル名2} ...
```

ステージングエリアからの削除。（ディレクトリにファイルは残る）
```
$ git rm --cached {ファイル名1} {ファイル名2} ...
```

## mv

ファイル名の変更
```
$ git mv {今のファイル名} {変更したいファイル名}
```

ファイルの移動
```
$ git mv {移動させるフェイル名} {移動先のディレクトリのパス}
```

## log

ログの出力
```
$ git log
```

オプション・制限は[こちら](https://github.com/laika90/b2multicopter/blob/document/documents/git/02_git_terms.md#git-log)

## clone

リポジトリのクローン
```
$ git clone {リポジトリのURL}
```
`git clone`の際に起きるトラブルへの対処は[こちら](https://github.com/laika90/b2multicopter/blob/document/documents/trouble_shooting/git_clone_in_raspberrypi.md)

## branch 作成・移動

サーバー名はoriginにしときます  

ローカルに新しいブランチを作成
```
$ git branch <ブランチ名>
```

ブランチのプッシュ
```
$ git push origin <ブランチ名>
```

ブランチの移動
```
$ git checkout <ブランチ名>
```

ブランチを作成して移動( branch + checkout )
```
$ git checkout -b <ブランチ名>
```

新しく<ブランチ>を作る以外にも，チェックアウトしたいブランチが  
(a)まだローカルに存在せず  
(b)存在するリモートが1つだけ  
の場合、自動で追跡ブランチを作ってくれる。要約すると、他人が作ったブランチに入りたい時。
```
$ git checkout <ブランチ名>
```

## branchの確認

ローカルブランチの表示
```
$ git branch
```

ローカルブランチの全表示（リモート追跡ブランチ含）
```
$ git branch -a
```

リモートブランチの表示
```
$ git branch -r
```

## branchの削除

ローカルブランチの削除
```
$ git branch -d <ブランチ名>
```

リモートブランチの削除
```
$ git push origin --delete <ブランチ名>
```
または
```
$ git push origin:<ブランチ名>
```

同期（他人が削除したリモートブランチがまだ自分のローカルに残ってる）
```
$ git fetch -p
```

リモートブランチ削除済みの場合に，リモート追跡ブランチの削除。  
これはリモートブランチがマージ&削除された時点で使用可能。  
(git fetch -p でも消せるのであんまり需要ないかも)
```
$ git remote prune origin
```

## branchの名前の変更

名前の変更
```
$ git branch -m <古い名前> <新しい名前>
```

## 差分の確認  

現在のブランチと<ブランチ>との差分の確認
```
$ git diff <ブランチ名>
```  

ブランチAとブランチBの差分の確認
```
$ git diff <ブランチA> <ブランチB>
```  

ブランチAとブランチBの差分のファイル名のみ確認
```
$ git diff --name-only <ブランチA> <ブランチB>
```  

ブランチAとブランチBのファイルの差分の確認
```
$ git diff <ブランチA>:<ファイル名> <ブランチB>:<ファイル名>
```

上の場合で，ファイル名が同じ場合
```
$ git diff <ブランチA> <ブランチB> <ファイル名>
```

差分が多い時は，必要に応じてリダイレクトやパイプを用いましょう。
