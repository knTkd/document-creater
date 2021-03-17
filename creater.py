import os
import shutil
from tkinter import filedialog


class Appender:

    def __init__(self, input_filepath='input.txt', origin_filepath='origin.html', created_filepath='created.html'):
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
        # 空行もしくはspaceだけの行を消す
        self.input_lines = [il for il in self.input_lines if il.replace(' ', '') != '']

        # originファイルの何行目に埋め込むかを探す
        self.insert_line = self.find_insert_line()

        # 各行のインデントレベルをリストで持つ
        self.indent_levels = [self.count_indent(il) for il in self.input_lines]

        # 各行のインデントレベルが局所的な底であるかどうかをbool列で持つ
        self.local_bottom = [False] * len(self.indent_levels)
        for i, indent_level in enumerate(self.indent_levels[1:-1], 1):
            if self.indent_levels[i - 1] <= indent_level >= self.indent_levels[i + 1]:
                self.local_bottom[i] = True
        self.local_bottom[0] = self.indent_levels[0] >= self.indent_levels[1]
        self.local_bottom[-1] = self.indent_levels[-1] >= self.indent_levels[-2]

        self.raw_lines = list()

    def go(self):
        # convert input_lines to on html
        self.html_for_append = self.convert_input_lines()

        # append all
        self.append_all()

        # createdファイルに書き込む
        with open(self.created_file, mode='w') as f:
            f.writelines(self.created_lines)


    def append_all(self):
        for for_append in self.html_for_append:
            self.append_htmltext(for_append)

    def index_list2str(self, indent_level, index_list): 
        if indent_level == 0:  return ''
        r = ''
        for index in index_list[1:indent_level+1]:
            r += str(index) + '-'
        return r[:-1] + '. '

    def next_index_list(self, pre_il, il, index_list):
        # インデックスを１つ進める
        # 例 2-3-1  ->  2-3-2
        r = index_list[::]
        if pre_il == il:
            r[il] += 1
        elif pre_il > il:
            r[il] += 1
            for i in range(il + 1, len(r)):
                r[i] = 1
        else:
            pass
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

    def input2raw(self, input_line):
        return self.n2br(self.pruning(input_line))

    def raw2code(self, text):
        return '<pre class="code">' + text + '</pre>'

    def raw2html(self, text, indent_level):
        # 生テキストをhtmlに変換する関数

        text = '<h' + str(indent_level+1) + '>' + text + '</h' + str(indent_level+1) + '>'
        if indent_level == 0:
            text = '<hr>' + text + '<hr>'
            
        return text

    def n2br(self, text):
        # \n -> <br>
        raw_text = repr(text)[1:-1]  # rawにしてるので前後に'が付く
        return raw_text.replace(r'\\n', '<br>')
    
    
    def pruning(self, text):
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

    def find_lowest_indent(self):
        # input.txtの中で一番低いインデントの数値を返す 一番低いのは<h->を付けない
        r = 0
        for input_line in self.input_lines:
            r = max(r, self.count_indent(input_line))
        return r

    def nspace(self, n):
        return '  ' * n

    def append_htmltext(self, htmltext):
        # コードをcreated_linesに埋め込む
        self.created_lines.insert(self.insert_line, self.nspace(self.indent) + htmltext + '\n')
        self.insert_line += 1
        
    def find_insert_line(self):
        for line, text in enumerate(self.origin_lines):
            if '</body>' in text:
                return line
        print(f'error: origin.htmlファイル内に</body>が見当たりません')
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
    kwargs['created_filepath'] = os.path.join(basedir, 'created', 'document.html')

    if not os.path.exists(os.path.dirname(kwargs['created_filepath'])):
        os.mkdir(os.path.dirname(kwargs['created_filepath']))
    
    
    appender = Appender(**kwargs)
    appender.go()

    shutil.copy(os.path.join(basedir, 'style.css'), os.path.join(basedir, 'created', 'style.css'))
    print(f"\nhtmlへ変換しました. ({kwargs['created_filepath']})\nファイルアイコンをダブルクリックするとブラウザで開くことができます")

if __name__ == '__main__':
    main()
