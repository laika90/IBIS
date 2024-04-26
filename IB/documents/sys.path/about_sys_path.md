# sys.path を用いてパスを通す方法

## 目次

・python ライブラリ 『sys』について  
・モジュールの検索と sys.path  
・sys.path に 自作モジュールの path をappend して別ディレクトリで import する方法  
・sys.path を用いる注意点と解決策  
・参考サイト  

### python ライブラリ 『sys』について

`sys`はPythonのインタプリタや実行環境に関する情報を扱うためのライブラリ。  
使用しているプラットフォームを調べる時や、スクリプトの起動パラメータを取得する場合などに利用する。  
標準ライブラリである。

### モジュールの検索と sys.path

import文があったときに、Pythonはビルトインモジュール（一部・・の標準ライブラリ。sysなど）を検索し、見つからなかったときにsys.path（list 型）に入っているパスから順に探していく。  
実際に見てみると

```python
import sys
print(sys.path)
```

実行結果

```python
['/Users/matsushimakouta/program/pystudy/test', '/opt/homebrew/Cellar/python@3.11/3.11.4/Frameworks/Python.framework/Versions/3.11/lib/python311.zip', '/opt/homebrew/Cellar/python@3.11/3.11.4/Frameworks/Python.framework/Versions/3.11/lib/python3.11', '/opt/homebrew/Cellar/python@3.11/3.11.4/Frameworks/Python.framework/Versions/3.11/lib/python3.11/lib-dynload', '/Users/matsushimakouta/Library/Python/3.11/lib/python/site-packages', '/opt/homebrew/lib/python3.11/site-packages', '/opt/homebrew/Cellar/pybind11/2.10.4/libexec/lib/python3.11/site-packages']
```

`/Users/matsushimakouta/program/pystudy/test`というのがカレントディレクトリ。sys.pathに自動的にカレントディレクトリが入っていることから、同階層のモジュールは直で import できるということがわかる。

pystudy/test/test_lib.py

```python
def is_imported():
    return True
```

pystudy/test/import_mymojule_test.py

```python

import test_lib

if test_lib.is_imported():
    print("OK")
```

実行結果

```python
OK
```

### sys.path に 自作モジュールの path をappend して別ディレクトリで import する方法

list 型である sys.path に自作モジュールのパスがあれば良いので、これを append する。

pystudy/test_dir/libtest.py

```python
print("import clear")
```

pystudy/test/sys_import.py

```python
import sys

print(sys.path)
sys.path.append("/Users/matsushimakouta/program/pystudy/test_dir")
print(sys.path)
import libtest
```

実行結果

```python
['/Users/matsushimakouta/program/pystudy/test', '/opt/homebrew/Cellar/python@3.11/3.11.4/Frameworks/Python.framework/Versions/3.11/lib/python311.zip', '/opt/homebrew/Cellar/python@3.11/3.11.4/Frameworks/Python.framework/Versions/3.11/lib/python3.11', '/opt/homebrew/Cellar/python@3.11/3.11.4/Frameworks/Python.framework/Versions/3.11/lib/python3.11/lib-dynload', '/Users/matsushimakouta/Library/Python/3.11/lib/python/site-packages', '/opt/homebrew/lib/python3.11/site-packages', '/opt/homebrew/Cellar/pybind11/2.10.4/libexec/lib/python3.11/site-packages']
['/Users/matsushimakouta/program/pystudy/test', '/opt/homebrew/Cellar/python@3.11/3.11.4/Frameworks/Python.framework/Versions/3.11/lib/python311.zip', '/opt/homebrew/Cellar/python@3.11/3.11.4/Frameworks/Python.framework/Versions/3.11/lib/python3.11', '/opt/homebrew/Cellar/python@3.11/3.11.4/Frameworks/Python.framework/Versions/3.11/lib/python3.11/lib-dynload', '/Users/matsushimakouta/Library/Python/3.11/lib/python/site-packages', '/opt/homebrew/lib/python3.11/site-packages', '/opt/homebrew/Cellar/pybind11/2.10.4/libexec/lib/python3.11/site-packages', '/Users/matsushimakouta/program/pystudy/test_dir']
import clear
```

確かに test_dir への path が通り、import できた。

### sys.path を用いる注意点と解決策

path を絶対パスで通した場合、人によって前半部分が異なるため大きな問題になってしまう。

```python
/Users/matsushimakouta/program/pystudy/test_dir
```

この場合、pystudy 以降が git ディレクトリだとして、その前のパスが通らなくなってしまうということ。相対パスを用いるとコード実行のディレクトリが限定されてしまうためよくない。  
『Poetry なり requirements.txt を使って自作モジュールを読み込みましょう。』とのこと。[参考文献(2)]  
他にも簡易的なやり方が二つほど紹介されていた。[参考文献(1)]

### 参考サイト

(1)[別ディレクトリの自作モジュールをimport](https://fuji-pocketbook.net/another-dir-module/)  
(2)[sys.path.appendを使わないでください](https://qiita.com/siida36/items/b171922546e65b868679)