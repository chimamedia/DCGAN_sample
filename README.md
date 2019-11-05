# DC-GAN
- DC-GANのサンプルプログラムになります。

- [GANについて概念から実装まで　～DCGANによるキルミーベイベー生成～](https://qiita.com/taku-buntu/items/0093a68bfae0b0ff879d)さんのプログラムを少し改良しております。
- 下のサンプルコードになります。[Github](https://github.com/taku-buntu/Keras-DCGAN-killmebaby)

# Envirovment
- 使用した環境は以下の通りです。
  - OS
    - Windows 10
  - Hardware
    - Memory 32GB
    - GPU NVIDIA GeForece GTX 1080Ti 11GB
  - Software
    - Python 3.7.3
    - tensorflow-gpu 1.13.1
    - CUDA 10.1
    - cudnn v7.6.3.30 (CUDA 10.1)

# Usage
- プログラムの起動は以下の通りです。
  - サンプルでは，アイドルの画像を生成するようになります。
  - 画像は適当に拾ってきている画像です。
  - デフォルトの値として以下のようになっています。
    - iterations: 10000
    - save point: 1000
    - save image: idol_gans
  - プログラム引数
    - -p: 読み込むフォルダの指定（オリジナル画像用）
    - -w: 出力フォルダ
    - -i: イテレーション数
    - -s: 出力ポイントの場所
  
```
python .\dcgan.py
```
## Results


# Using original images
- オリジナルの画像を用いて、DCGANを利用するためには以下の条件を満たしてください。
  - 画像サイズ: 128×128
- フォルダの構成
  - 例えば、車を対象として、会社ごとに分ける場合
    - car－nissan
    -  ｜－honda
    -  ｜－toyoya
  - 1つのフォルダのみでも可
    - car－car

- 作成したオリジナルのフォルダ（例としてcar）で識別する場合

```
python .\dcgan.py -p .\car
```
