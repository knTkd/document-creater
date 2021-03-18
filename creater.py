import os
import shutil
from tkinter import filedialog


class Appender:

    def __init__(self, input_filepath='input.txt', origin_filepath='origin.html', created_filepath='created/document.html'):
        # 埋め込むときの元となるインデント
        self.indent = 1

        # 各ファイルの名前をセット
        self.input_file = input_filepath
        self.origin_file = origin_filepath
        self.created_file = created_filepath
        
        # originファイルをリストとして読み込み
        self.origin_lines = self.readlines(self.origin_file)
        # createdとしてコピー
        self.created_lines = self.origin_lines[::]
        # inputファイルをリストとして読み込み
        self.input_lines = self.readlines(self.input_file)

        # spaceをすべて半角に変換し、文末の\nを消す
        self.input_lines = [il.replace('　', ' ')[:-1] for il in self.input_lines]
        # 空行もしくはspaceだけの行を排除する
        self.input_lines = [il for il in self.input_lines if il.replace(' ', '') != '']

        # ====================   それぞれのリストを作成   =======================
        # コードかどうかをbool列で持つ
        self.is_codes = [self.prun_head_space(il).find('code') == 0 for il in self.input_lines]

        # 各行のhtml要素を作る時に入れる生文をリストで持つ
        self.raw_lines = self.inputs2raws(self.input_lines)

        # 各行のインデントレベルをリストで持つ
        self.indent_levels = [self.count_indent(il) for il in self.input_lines]

        # 各行のインデントレベルが局所的な底であるかどうかをbool列で持つ
        self.is_local_bottoms = self.levels2bottoms(self.indent_levels)

        # 1-2-1のような索引をつくる(str)
        self.indexes = self.levels2indexes(self.indent_levels)
        # 一番上のインデントレベルは索引なしにする それ以外の索引は１つレベルを下げる
        for i in range(len(self.indexes)):
            if self.indexes[i] == '1':
                self.indexes[i] = ''
            else:
                self.indexes[i] = self.indexes[i][2:]
        # =======================================================================

        # originファイルの何行目に埋め込むかを探す
        self.insert_line = self.find_insert_line()


    def go(self):
        html_lines = self.convert_to_html()

        # append all
        self.append_html_lines(html_lines)

        # createdファイルに書き込む
        with open(self.created_file, mode='w') as f:
            f.writelines(self.created_lines)
    
    def append_html_lines(self, html_lines):
        for html_line in html_lines:
            append_line = self.nspace(self.indent) + html_line + '\n'
            self.created_lines.insert(self.insert_line, append_line)
            self.insert_line += 1

    def convert_to_html(self):
        # 各リストからhtmlの要素を作って返す
        r = list()
        for i in range(len(self.raw_lines)):
            html_line = self.raw_lines[i]
            if self.is_codes[i]:
                html_line = self.raw2code(html_line)
            if self.is_codes[i] or self.is_local_bottoms[i]:
                r.append(html_line)
                continue

            if self.indexes[i] == '':
                html_line = self.addhr(html_line)
            else:
                # 1-2-1. なになに〜とする
                html_line = self.indexes[i] + '. ' + html_line
            html_line = self.raw2html(html_line, self.indent_levels[i])
            r.append(html_line)
        return r

    def raw2code(self, text):
        return '<pre class="code">' + text + '</pre>'

    def raw2html(self, text, indent_level):
        # 生テキストをhtmlに変換する関数
        h_elm = min(6, indent_level + 1)
        text = '<h' + str(h_elm) + '>' + text + '</h' + str(h_elm) + '>'
        return text

    def addhr(self, text):
        return '<hr>' + text + '<hr>'


    # ==================  __init__ で使ってるもろもろの関数  ====================
    
    def levels2indexes(self, indent_levels):
        # インデントレベルノリストから3-3-2のような索引のリストを返す(str)
        index_list = [1] * 10
        r = list()
        indent_levels = [indent_levels[0] - 1] + indent_levels
        for cur, pre in zip(indent_levels[1:], indent_levels[:-1]):
            if cur <= pre:
                index_list[cur] += 1
            if cur < pre:
                for i in range(cur + 1, len(index_list)):
                    index_list[i] = 1
            r.append(self.numlist2index(index_list[:cur + 1]))
        return r
    


    def numlist2index(self, nlist):
        # [1, 2, 4] :  '1-2-4'
        sep = '-'
        return sep.join(map(str, nlist))
        

    def levels2bottoms(self, indent_levels):
        # インデントレベルのリストから局所的な底であるかどうかのBoolリストを返す
        on_decrease = True
        last_down_idx = 1
        r = [False] * len(indent_levels)
        indent_levels.append(-1)  # 一番最後に強制的に上げることで未処理がないように
        for i, (cur, pre) in enumerate(zip(indent_levels[1:], indent_levels[:-1]), 1):
            if cur < pre and on_decrease:
                on_decrease = False
                for j in range(last_down_idx, i):
                    r[j] = True
            elif cur > pre:
                on_decrease = True
                last_down_idx = i
        return r
    
    def inputs2raws(self, input_lines):
        # 入力ファイルをもらってhtml要素で入れる生文のリストを返す
        # '   これが\nこうじゃ！'  ===>>>  'これが<br>こうじゃ！'
        # '  code print('hehe')'   ===>>>  'print('hehe')'
        r = list()
        for input_line in input_lines:
            rawline  = self.n2br(self.prun_head_space(input_line))
            if rawline.find('code') == 0:
                rawline = rawline[5:]
            r.append(rawline)
        return r
        # return self.n2br(self.pruning(input_line))

    def make_table(self):
        # self.indent_level と self.raw_linesを使って目次のhtmlを作る
        r = list()
        r.append('<div class="table">')
        r.append('  <ol>')
        r.append('    <li><a href="#' + '')
        

        r.append('  </ol>')
        r.append('</div>')
        return r
    
    def convert_input_lines(self):
        # self.input_linesを埋め込む文字列としてのhtmlに変換する
        
        pre_indent_level = -1  # 前のインデントレベル
        index_list = [1] * 6   # 今のインデックスの番号をリストで持つ
        r = list()
        for indent_level, input_line, local_bottom in zip(self.indent_levels, self.input_lines, self.local_bottom):
            index_list = self.next_index_list(pre_indent_level, indent_level, index_list)
            raw_line = self.input2raw(input_line)
            if raw_line.find('code ') == 0:
                html_line = self.raw2code(raw_line[5:])
                raw_line = ''
            elif local_bottom:
                html_line = raw_line
                raw_line = ''
            else:
                raw_line = self.index_list2str(indent_level, index_list) + raw_line
                html_line = self.raw2html(raw_line, indent_level)
            r.append(html_line)

            # 目次用にraw_lineを取っておく (コードとボトムは空文字として)
            self.raw_lines.append(raw_line)

            pre_indent_level = indent_level
        return r

    def n2br(self, text):
        # \n -> <br>
        raw_text = repr(text)[1:-1]  # rawにしてるので前後に'が付く
        return raw_text.replace(r'\\n', '<br>')
    
    
    def prun_head_space(self, text):
        # 先頭のの空白を捨てる(pruningは剪定のこと)
        while text[0] == ' ' or text[0] == '　':
            text = text[1:]
        return text

    def count_indent(self, text):
        # インデントのレベルを調べる(先頭の空白の数を調べる)
        r = 0
        while text[r] == ' ' or text[r] == '　':
            r += 1
        return r

    def nspace(self, n):
        return '  ' * n

    def find_insert_line(self):
        for line, text in enumerate(self.origin_lines):
            #if '</body>' in text:
            if '<!-- 生成したコード -->' in text:
                return line + 1
        print(f'error: origin.htmlファイル内に<!-- 生成したコード -->が見当たりません')
        exit(1)

    def readlines(self, filepath):
        # filepathをもらって、中身を行ごとのリストで返す
        r = None
        try:
            with open(filepath) as f:
                r = f.readlines()
        except:
            print(f'{filepath} が見つかりません\n')
            raise
        return r
    

def main():
    input('変換する元となる、ソースファイルを選択してください （準備が良ければエンターボタン）')

    kwargs = dict()

    # typ = [('てきすとふぁいる', '*.txt')]
    typ = [('', '*')]
    kwargs['input_filepath'] = filedialog.askopenfilename(filetypes=typ, initialdir='.')

    basedir = os.path.dirname(os.path.abspath(__file__))

    kwargs['origin_filepath'] = os.path.join(basedir, 'origin.html')
    created_filename = input('生成されるhtmlファイルの名前を拡張子なしで入力してください（そのままエンターを押すとデフォルトのdocument.htmlで保存されます）')
    if created_filename == '':  created_filename = 'document'
    
    kwargs['created_filepath'] = os.path.join(basedir, 'created', created_filename + '.html')

    if not os.path.exists(os.path.dirname(kwargs['created_filepath'])):
        os.mkdir(os.path.dirname(kwargs['created_filepath']))
    
    
    appender = Appender(**kwargs)
    appender.go()

    shutil.copy(os.path.join(basedir, 'style.css'), os.path.join(basedir, 'created', 'style.css'))
    print(f"\nhtmlへ変換しました. ({kwargs['created_filepath']})\nファイルアイコンをダブルクリックするとブラウザで開くことができます")

if __name__ == '__main__':
    main()
