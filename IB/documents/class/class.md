# __classについて__
## __オブジェクト指向とは__
---
### __なにそれ？__
簡単に言うと __いくつもの"オブジェクト（もの）"をつくり、それらを組み合わせて何かを完成させること。__
![d181886eeab347512723fac424df768ac691d587522b689a6894a0a341f0d239](https://user-images.githubusercontent.com/131977893/235936338-ead71640-fba0-44c2-a1df-d5304f392f11.jpeg)

### __メリット__
__プログラムがわかりやすくなる__
オブジェクト指向では「モノ」とその「役割」を決める

例:

![ed1f353a814489816e4a5c59495f43420bc8833aaacf42d38386c038b93fe6fb](https://user-images.githubusercontent.com/131977893/235936358-168ea0b7-d6f8-4648-93bd-817c3fce6af0.jpeg)
  

敵に新たに"MP"を追加することになったら従来の方法では大変！

なぜならそれぞれに追加しなければならないから。

__もの毎にわけて、役割をまとめて書く！__

オブジェクトは自分の処理の仕方を自分で知っている。

データのまとまりに、そのデータの処理の仕方も一緒にカプセルに入れるということ。  
データに処理方法がくっついているのでデータの内容毎に違う処理を書かなくてよくなる。  

### __classとは__

オブジェクトの内容を記述しておく仕組みがclass。

### __メソッドとは__

classの中で処理の仕方を書いてある部分。メソッドの中では自身のデータを参照できる。

### __インタンス化とは__

ひな型から実際のデータを格納したものを作り、データを保存すること。

## __classの使い方__
---
### __classの定義__
```python
class SimpleData: #データを2つ持っている
    a=0
    b=0

    def sum(self):　#メソッドを2つ持っている（sumとset）、第一引数にselfを書く。インデントを下げる。
        return self.a + self.b

    def set(self, a, b):
        self.a = a #selfは自分自身の変数に、という意味。全て全く違う変数。
        self.b = b
```

### __classのインスタンス化とインスタンス変数__
```python
data1 = SimpleData()  #data1, data2をインスタンス変数という
data2 = SimpleData()
data1.set(1,2)
data2.set(3,4)
print(data1.sum())
print(data2.sum())
```
```python
3
7
```
メソッドの中ではselfで自身の持つデータにアクセスできる。また引数でもらった変数を参照することもできる。

### __コンストラクタとは__
__コンストラクタ__：インスタンス化された時に最初に呼ばれる特別なメソッド。
データの初期化の処理を書く。
```python
class SimpleData: 

    def __init__(self, a, b): 
        self.a = a
        self.b = b

    def sum(self):　
        return self.a + self.b

    def set(self, a, b):
        self.a = a 
        self.b = b

data1  = SimpleData(1, 2)
print(data1.sum())
```
```python
3
```
ここで
```python
    def __init__(self, a, b)
```
の前に
```python
    def __init__(self):
        self.a = 0
        self.b = 0
```
を入れて、（引数は与えなくても良い！）
```python
data2  = SimpleData()
print(data2.sum())
```
を実行しようとしてもエラーが出てしまう。Pythonではどのコンストラクタが呼ばれるかは後に書いたものが優先されるよう。
値を与えなかったら0にするときは次のコードにすれば良い。
```python
    def __init__(self, a = 0, b = 0)
        self.a = a
        self.b = b
```

### __デストラクタとは__
__デストラクタ__ ：インスタンスがどこからも参照されなくなった時に呼ばれる特別なメソッド。
```python
class SimpleData: 

    def __init__(self, a, b):
        self.a = a
        self.b = b

    def __del__(self):
        print("インスタンスが破棄されました。")

    def sum(self):　
        return self.a + self.b

    def set(self, a, b):
        self.a = a 
        self.b = b

data1=SimpleData(1,2)
print(data1.sum())
data1=None
```
```python
3
インスタンスが破棄されました。
```
実際にはあまり使うことはないらしい。コンストラクタでファイルを開いていたとか何かのリソースを予約している場合、そのリソースの破棄の処理をデストラクタに書いたりする。
### __classの継承とは__
より一般的なclassを受け継いで、、より専門的なclassを作ること。
```python
class ComplexData(SimpleData):

    def __init__(self, a, b): #引数ありでインスタンス化された時に呼ばれるコンストラクタ
        super().__init__(a, b)
        self.c = 1 #cの値を外から初期化することはできない！
     
    def sum(self):
        return self.a + self.b + self.c
data3 = ComplexData(4,5)
print(data3.sum())
```
```python
10
```
## __注意点やコツ__
継承しすぎると継承元をどこまでも遡れるようになり、どのクラスのデータを参照しているのかわからなくなる・・・__継承地獄__

本当に処理が変わった時のみ継承するようにしたほうがいい。
