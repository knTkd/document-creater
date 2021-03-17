# Pythonでドキュメントジェネレータを作ってみた
職場で全くの初心者向けにPythonやいくつかのコマンドを教える資料を作っていたけど、いちいち<h1>〜やら<span>〜やらを打つのがだるすぎて一から作ってみることにした
職場のパソコンにはPythonの実行環境は有るのでPythonにて

# 使い方
## だいたいの説明
入力として１つのファイルを与えます 
そのファイルのインデントに沿って、h1-6に応じたタグが割り当てられる

## 例
### inputファイル
以下のファイルを与えたとすると
```text:input.txt
はじめに
　目的
　　もくてき〜〜〜〜〜〜〜〜〜〜〜〜
　準備
　　準備〜〜〜〜〜〜〜〜〜〜〜〜〜〜〜〜

```(

### createdファイル
次のようにhtmlが生成される
```html:created.html
  <hr><h1>はじめに</h1><hr>
  <h2>1. 目的</h2>
  もくてき〜〜〜〜〜〜〜〜〜〜〜〜
  <h2>2. 準備</h2>
  準備〜〜〜〜〜〜〜〜〜〜〜〜〜〜〜〜
```(

### コードの埋め込み
また、以下のようにコードを埋め込むことも可能である。
コードを埋め込む際には先頭に `code ` をつける必要が有る
```python:input.txt
code name = input()\nprint(f'Hello, {name}')
```(
次のように、htmlの要素が出力される
```html:created.html
 <pre class="code">name = input()<br>print(f'Hello, {name}')</pre>
```(

### input.txtを元にして作成されたHTMLの例 [リンク](https://github.com/knTkd/document-creater/created/document.html)

### ローカルでのパス
education-material/createdByPy/