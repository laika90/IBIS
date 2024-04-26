# まだ間に合っちゃうCMakeその1

## 参考にしたサイト

* [CMakeの使い方（その1）](https://qiita.com/shohirose/items/45fb49c6b429e8b204ac)  
* [CMakeの使い方（その2）](https://qiita.com/shohirose/items/637f4b712893764a7ec1)  
* [CMakeの使い方（その3）](https://qiita.com/shohirose/items/d2b9c595a37b27ece607)  

全部同じ方の記事ですがとてもわかりやすかったのでこれをまとめました。~~（いやもうこれ読めって）~~  

まとめた、というかコピペ。

## cmakeとは

ビルドのためのツール。コンパイラに依存しない。CMakeListというものを作れば勝手にワンポチビルド。便利。

## ステップ1 : 実行ファイルの作成

### こんなものがありました

ディレクトリ構成
```
.
├── main.cpp
├── hello.hpp
└── hello.cpp
```

各ファイルたち
```cpp:main.cpp
// main.cpp

#include "hello.hpp"

int main()
{
    hello();
}
```

```cpp
// hello.hpp

// 2重include防止. おまじない.
#ifndef _HELLO_H_ 
#define _HELLO_H_

// プロトタイプ宣言
void hello();

#endif
```

```cpp
// hello.cpp

#include <iostream>
#include "hello.hpp"

// 関数の定義
void hello()
{
    std::cout << "hello" << std::cout;
}
```

### CLIでビルド

CLIでビルドしてみます。コンパイラはg++。僕はclangだけども。

打つべきコマンドは、
```bash
// ソースファイルのコンパイル。これでオブジェクトファイルができる（main.o, hello.o）
$ g++ -c main.cpp hello.cpp

// オブジェクトファイルをリンクして実行可能ファイルを作成。
$ g++ -o main main.o hello.o
```

すると、ディレクトリ構成は
```bash
.
├── main      # 実行可能ファイル
├── main.o    # オブジェクトファイル
├── hello.o
├── main.cpp  # ソースファイル・ヘッダファイル
├── hello.hpp
└── hello.cpp
```
となります。

実行は、
```
$ ./main
>>> hello
```
となります。

または、オブジェクトファイルの生成をしないなら、
```
$ g++ -o main main.cpp hello.cpp
```
でも良いですね。

### CMakeでビルド

さてこれを、CMakeによってビルドしましょう。ビルド設定は`CMakeLists.txt`に書くので、ディレクトリ構成は、

ディレクトリ構成
```
.
├── CMakeLists.txt
├── main.cpp
├── hello.hpp
└── hello.cpp
```
となりますね、

`CMakeLists.txt`の中身は、
```CMake
# CMakeのバージョン
cmake_minimum_required(VERSION 3.13)

# プロジェクト名と使用する言語を設定. project(名前 言語).
project(test_cmake CXX)

# a.outという実行ファイルをmain.cppとhello.cppから作成
add_executable(a.out main.cpp hello.cpp)
```

CMakeによるビルドの際には、ビルド専用ディレクトリを作成します。
```
$ cmake -S . -B build
$ cmake --build build
```

<details><summary>上のコードの意味（折りたたみ）</summary>

</br>

初めのは、ビルドシステムの指定をしています。

```
$ cmake -S <ソースツリー>
```
でソースツリー（ソースファイルとかがあるところ）の指定。

```
$ cmake -B <ビルドツリー>
```
でビルドツリー（ビルド専用ディレクトリがあるところ）の指定。  
もしビルドディレクトリがないなら、勝手に作ってくれる。

なのでまとめると、
```
$ cmake -S <ソースツリー> -B <ビルドツリー>
```
これによって`mkdir build``cd build``cmake ...`とかやらんで良くなる。

なのでさっきのコードの一個目は、
```
$ cmake -S . -B build
// $ cmake -S <カレントディレクトリ> -B <同階層にbuildディレクトリ(ないなら作ってね)>
```
という意味です。

二つ目ついては、
```
$ cmake --build <ビルドツリー>
```
でビルド実行ができる。ターミナルからなら、`make`の方が早い。  

(参考にしたサイト : [ここで差がつく cmake TIPS](https://qiita.com/osamu0329/items/0a72ee32ee6934a7edf7))

</details>

ビルドが終わると、
```bash
.
├── CMakeLists.txt
├── main.cpp
├── hello.hpp
├── hello.cpp
└── build
    ├── a.out         # 実行可能ファイル
    └── その他いろいろ

```

となります。`build`ディレクトリの中に諸々全部入るので、これを消せば初期状態に戻れます。（out-of-sourceビルド、とかいうらしい）

## ステップ2 : 静的・共有ライブラリの作成

<details><summary>静的・共有ライブラリ？って人はこちら（折りたたみ）</summary>

</br>

C++のライブラリは大きく二種類あって、静的ライブラリと共有ライブラリ（=動的ライブラリ）別れます。

静的ライブラリ

> 複数のオブジェクトファイルをまとめたもの。リンク時に実行可能ファイルに結合される。静的ファイルのリンク = 静的リンク。`.lib`や`.a`が拡張子。リンク時に取り込まれるので、実行がお手軽かつ起動が早い。

共有ライブラリ

> 複数のプログラムが共通して利用する汎用性の高いライブラリ。リンク時には必要な情報のみリンク。実際のリンクは実行時にされる。そのため、配布などする際はライブラリと実行可能ファイルはどちらも渡さなければならない、Linuxでは`.so`、Windowsでは`.dll`が拡張子。プログラムの変更のお手軽さとサイズの小ささが利点。

僕たちが作るのは静的ライブラリですね。いや作らんかもしれん。

共有ライブラリの場合。
```bash
g++ -shared -fPIC -o share.so share.cpp
```
`-shared` ... 共有ライブラリを作成するオプション  
`-fPIC` ... プログラムの再配置回数を少なくして、実行速度の高速化を行うオプション

</details>

### やりたいこと

やりたいことが不透明なので、一旦まとめてみました。

```zsh
a.out
├── main.cpp
└── libgreetings.a or .so
    ├── hello.o       <- hello.cpp
    └── goodmorning.o <- goodmorning.cpp

# コンパイル元を表しています.
# .aは静的, .soは共有ライブラリの時です.
```

### 用意するもの

このようなコンパイルをしたいので、先のディレクトリ構成に加えて、`goodmorning.cpp`, `goodmorning.hpp`の追加、`main.cpp`の変更が必要になります。

```cpp
// goodmorning.hpp

#ifndef GOOD_MORNING_H
#define GOOD_MORNING_H

void good_morning();

#endif
```

```cpp
// goodmorning.cpp

#include <iostream>
#include "good_morning.hpp"

void good_morning() 
{
    std::cout << "Good morning" << std::endl;
}
```

```cpp
// main.cpp

#include "hello.hpp"
#include "good_morning.hpp"

int main () 
{
    hello();
    good_morning();
}
```

### 静的ライブラリの場合(CLI)

やることはこんな感じ。

* `hello.cpp`と`good_morning.cpp`をコンパイルしてオブジェクトファイルを生成
* できた`hello.o`と`goodmorning.cpp`から静的ライブラリ`libgreetings.a`を作成
* `main.cpp`のコンパイルの時に、`libgreetings.a`をリンクしてビルド

実際の作成手順としては、

```bash
# オブジェクトファイル(hello.o, good_morning.o)の作成
$ g++ -c hello.cpp good_morning.cpp           

# 静的ライブラリ(libgreetings.a)の作成
$ ar rvs libgreetings.a hello.o good_morning.o 

# main.cppをコンパイルしてlibgreetings.aとリンクし実行ファイルa.outを作成
$ g++ main.cpp libgreetings.a                   
```

となります。  

最終的なディレクトリ構成は省略します。

### 共有ライブラリの場合(CLI)

静的ライブラリと同じです。

```bash
# オブジェクトファイル(hello.o, good_morning.o)の作成
$ g++ -fPIC -c hello.cpp good_morning.cpp  

# 共有ライブラリ（libgreetings.so）の作成
$ g++ -shared hello.o good_morning.o -o libgreetings.so   

# main.cppをコンパイルしてlibgreetings.soとリンクし実行ファイルa.outを作成
$ g++ main.cpp -L. -lgreetings -Xlinker -rpath -Xlinker . 
```

書き方がとっても難しい()。

これで両方のCLIの場合はビルドが完了です。

どちらの`a.out`もちゃんと動くはずです。

```bash
$ ./a.out
>>> hello
>>> Good morning
```

### CMakeでやる場合

変更を加えるのは、`CMakeLists.txt`のみです。すばらすばら。

### 静的ライブラリの場合(CMake)

```CMake
# CMakeLists.txt

#さっきとおんなじ. プロジェクト名とバージョン設定.
cmake_minimum_required(VERSION 3.13)
project(test_cmake CXX)

# hello.cppとgood_morning.cppをコンパイルして静的ライブラリlibgreetings.aを作成
add_library(greetings STATIC hello.cpp good_morning.cpp)

# a.outという実行ファイルをmain.cppから作成
add_executable(a.out main.cpp)

# a.outを作成する際にlibgreetings.aをリンク
target_link_libraries(a.out greetings)
```

この後はステップ1と同様の手順でビルド。

なんかいけそうな気がする。

### 共有ライブラリの場合(CMake)

```CMake
# CMakeLists.txt

# さっきとおんなじ. プロジェクト名とバージョン設定.
cmake_minimum_required(VERSION 3.13)
project(test_cmake CXX)

# hello.cppとgood_morning.cppをコンパイルして共有ライブラリlibgreetings.soを作成
add_library(greetings SHARED hello.cpp good_morning.cpp)

# a.outという実行ファイルをmain.cppから作成
add_executable(a.out main.cpp)

# a.outを作成する際にlibgreetings.soをリンク
target_link_libraries(a.out greetings)
```

**静的ライブラリと共有ライブラリの相違点は、`STATIC`なのか`SHARED`かだけ。**

```CMake
add_library(greetings [SHARED|STATIC] hello.cpp good_morning.cpp)
```

コマンドラインの時の面倒なオプションはCMakeが全てやってくれる。

とても便利な予感。

### 静的・共有ライブラリの無指定

さっきは`STATIC`か`SHARED`かを明示しましたが、これをやらないとどうなるんでしょうか。

```CMake
add_library(greetings hello.cpp good_morning.cpp)
```

これはグローバルオプション`BUILD_SHARED_LIBS`の ON / OFF によって決まります。（デフォルトはOFF）（多分ONがSHARED、OFFがSTATIC）

すると、CMakeでビルドする際にオプション指定できます。

```bash
$ cmake -S . -B build -DBUILD_SHARED_LIBS=ON
$ cmake --build build
```

一般的には、各ライブラリごとに静的・共有ライブラリのどちらでビルドするか選択できるオプションを作成しておくべきらしい。そりゃそうか。

```CMake
# GREETINGS_BUILD_SHARED_LIBSというオプションを作成。デフォルトをOFFに設定。
option(GREETINGS_BUILD_SHARED_LIBS "build greetings as a shared library" OFF)

if (GREETINGS_BUILD_SHARED_LIBS)
  add_library(greetings SHARED hello.cpp good_morning.cpp)
else()
  add_library(greetings STATIC hello.cpp good_morning.cpp)
endif()
```

すると、コマンドラインから指定できる。
```bash
$ cmake -S . -B build -DGREETINGS_BUILD_SHARED_LIBS=ON
$ cmake --build build
```

## ステップ3 : サブディレクトリにソースが分散している場合

pico_copterではディレクトリ直下に全部のソースコードを置いていたような気がしますが、多分一般的には良くないんでしょう。

ということでライブラリを作る際には、各役割ごとにディレクトリを分けて管理するのが一般的です。

さて、さっきのディレクトリ構造をちょっと変えてみましょう。

```
.
├── include/ 
│   ├── hello.hpp
│   └── goodmorning.hpp
│
├── src/
│   ├── hello.cpp
│   └── goodmorning.cpp
│
└── test/
    └── main.cpp
```

### CLIでビルド

CLIでビルドしてみましょう。長旅です。

やり方としては、ルートディレクトリにいるものとして、共有ライブラリを作成、実行ファイルにリンク。

```bash
$ cd src
$ g++ -fPIC -c hello.cpp good_morning.cpp -I../include
$ g++ -shared *.o -o libgreetings.so
$ cd ../test
$ g++ main.cpp -I../include -L../src -lgreetings -Xlinker -rpath -Xlinker ../src
```

今回は`-L`に加えて、`-I`オプションでインクルードファイルを探すディレクトリを指定しないといけません。これはディレクトリが分かれているからですね。デフォルトでカレントディレクトリはインクルードファイルを探すディレクトリに入っているので、ステップ2では必要ありませんでした。

ディレクトリ構成は省略します。本当はあった方がいいんだけど、、

### CMakeでビルド

サブディレクトリが存在する場合、各ディレクトリごとに`CMakeLists.txt`を作ります、

```
.
├── CMakeLists.txt
│
├── include/ 
│   ├── hello.hpp
│   └── goodmorning.hpp
│
├── src/
│   ├── CMakeLists.txt
│   ├── hello.cpp
│   └── goodmorning.cpp
│
└── test/
    ├── CMakeLists.txt
    └── main.cpp
```

インクルードはいらないみたいです。コンパイルとは別の扱いなんですね。

さて、各`CMakeLists.txt`ですが、

* ルートディレクトリ　-> サブディレクトリの登録
* サブディレクトリ　-> 各ディレクトリのコンパイル方法の指定

をします。

ルートディレクトリにある`CMakeList.txt`（一番上のやつ）

```CMake
# /CMakeLists.txt

#　いつもの
cmake_minimum_required(VERSION 3.13)
project(test_cmake CXX)

# サブディレクトリを登録
add_subdirectory(src)
add_subdirectory(test)
```

各サブディレクトリにある`CMakeList.txt`

```CMake
# /src/CMakeLists.txt

# 共有ライブラリの作成
add_library(greetings
  SHARED
    hello.cpp
    good_morning.cpp
  )

# greetingライブラリのインクルードディレクトリを教えてあげる
# PROJECT_SOURCE_DIRはこのプロジェクトのルートディレクトリの絶対パス
target_include_directories(greetings
  PUBLIC ${PROJECT_SOURCE_DIR}/include
  )
```

```CMake
# /test/CMakeLists.txt

# a.outという実行ファイルをmain.cppから作成
add_executable(a.out main.cpp)

# a.outをコンパイルする際にgreetingsをリンクする
target_link_libraries(a.out greetings)
```

`add_library`及び`add_executable`の最初の引数を**「ターゲット」**と呼びます。（今回だと`greetings`とか`a.out`とか）

キーワード`PRIVATE` / `PUBLIC` / `INTERFACE`の意味は、「ターゲットのみに必要」か、「ターゲット+それに依存するターゲットに必要」か、それとも、「それに依存するターゲットのみに必要」なのか、です。

| キーワード | ターゲットに必要 | そのターゲットに依存するターゲットに必要 |  
| :---: | :---: | :---: |  
| PRIVATE | ◯ | × |  
| PUBLIC | ◯ | ◯ |  
| INTERFACE | × | ◯ |  

ちょっとわけわからんくなるので今回の場合について考えてみましょう。

`include`に含まれる、インクルードしたいファイル群は、

* `greetings`のコンパイルに使います（例えば、`hello.cpp`は`#include hello.hpp`を指定している）
* `a.out`のコンパイルに使います（例えば、`main.cpp`は`#include hello.hpp`を指定している）

この時、`greetings`は「ターゲット」、`a.out`は「それに依存するターゲット」にあたります。

なので、今回は`PUBLIC`を選択します。

`PRIVATE`を選択するのは、自分自身のビルドにのみ必要な時、`INTERFACE`を選択するのはmヘッダのみのライブラリに対して使います。

これが書けたら、ステップ1、ステップ2と同じ要領でビルドするだけです。

なんかいけそうな気がしてきました。

prev | [next](https://github.com/laika90/b2multicopter/blob/document/documents/cmake/cmake_2.md)







