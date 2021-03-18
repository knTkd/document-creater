import os
import shutil
from tkinter import filedialog


class Appender:

    def __init__(self, input_filepath='input.txt', origin_filepath='origin.html', created_filepath='created/document.html'):
        # 埋め込むときの元となるインデント
        self.indent = 1
        
        self.index_sep = '-'

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
        '''
        for i in range(len(self.indexes)):
            if self.indexes[i] == '1':
                self.indexes[i] = ''
            else:
                self.indexes[i] = self.indexes[i][2:]
        '''
        # =======================================================================

        # 目次をoriginファイルの何行目に埋め込むかを探す
        self.insert_line_table = self.find_insert_line_table()

        # originファイルの何行目に埋め込むかを探す
        self.insert_line = self.find_insert_line()


    def go(self):
        
        # 目次を作る
        table_contents = self.make_table()

        # raw_lineなどをもとにhtmlを作成
        html_lines = self.convert_to_html()

        table_contents = list(map(self.prepare_append, table_contents))
        html_lines = list(map(self.prepare_append, html_lines))
        if self.insert_line_table > self.insert_line:
            table_contents, html_lines = html_lines, table_contents
            self.insert_line, self.insert_line_table = self.insert_line_table, self.insert_line
        
        self.created_lines = self.created_lines[:self.insert_line_table] + table_contents + self.created_lines[self.insert_line_table:self.insert_line] + html_lines + self.created_lines[self.insert_line:]

        # createdファイルに書き込む
        with open(self.created_file, mode='w') as f:
            f.writelines(self.created_lines)

    def prepare_append(self, text):
        return self.nspace(self.indent) + text + '\n'

    def make_table(self):
        # self.indent_level と self.raw_linesを使って目次のhtmlを作る
        r = list()
        r_idx = 0
        r_idx, r = self.elem_insert(r_idx, r, 'ul')
        indent_levels = [-1] + self.indent_levels
        for i, (cur, pre) in enumerate(zip(indent_levels[1:], indent_levels[:-1])):
            if self.is_local_bottoms[i] or self.is_codes[i]:
                continue
            if cur > pre:
                r_idx, r = self.elem_insert(r_idx, r, 'ul')
                r_idx, r = self.elem_insert(r_idx, r, 'li')
            else:
                r_idx += (pre - cur + 1)
                r_idx, r = self.elem_insert(r_idx, r, 'li')
            
            a_str = '<a href=#' + self.indexes[i] + '>' + self.raw_lines[i] + '</a>'
            r.insert(r_idx, a_str)
            r_idx += 1
        return r

    def elem_insert(self, idx, lines, tag):
        # linesにidx位置で<tag></tag>をいい感じにインサートする
        # 戻り値は新しいidxと入れたリスト
        # elem_insert(1, ['<ul>', '</ul>'], 'li')
        # (2, ['<ul>', '<li>', '</li>' '</ul>'])  returned
        lines.insert(idx, '</' + tag + '>')
        lines.insert(idx, '<' + tag + '>')
        return (idx + 1, lines)

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

            if self.indexes[i].isdigit():
                html_line = self.addhr(html_line)
            else:
                # 1-2-1. なになに〜とする
                html_line = self.indexes[i][self.indexes[i].find(self.index_sep) + 1:] + '. ' + html_line
            html_line = self.raw2html(html_line, self.indent_levels[i], id=self.indexes[i])
            r.append(html_line)
        return r

    def raw2code(self, text):
        return '<pre class="code">' + text + '</pre>'

    def raw2html(self, text, indent_level, id=''):
        # 生テキストをhtmlに変換する関数
        h_elm = min(6, indent_level + 1)
        text = '<h' + str(h_elm) + ' id=' + id + '>' + text + '</h' + str(h_elm) + '>'
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
        return self.index_sep.join(map(str, nlist))
        

    def levels2bottoms(self, indent_levels):
        # インデントレベルのリストから局所的な底であるかどうかのBoolリストを返す
        on_decrease = True
        last_down_idx = 1
        r = [False] * len(indent_levels)
        levels = indent_levels + [-1] # 一番最後に強制的に上げることで未処理がないように
        for i, (cur, pre) in enumerate(zip(levels[1:], levels[:-1]), 1):
            if cur < pre and on_decrease:
                on_decrease = False
                # 最後に下がったところから今の地点までを全部Trueに
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
            if '<!-- 生成したコード -->' in text:
                return line + 1
        print(f'error: origin.htmlファイル内に<!-- 生成したコード -->が見当たりません')
        exit(1)

    def find_insert_line_table(self):
        for line, text in enumerate(self.origin_lines):
            if '<!-- 目次 -->' in text:
                return line + 1
        print(f'error: origin.htmlファイル内に<!-- 目次 -->が見当たりません')
        exit(1)

    def readlines(self, filepath):
        # filepathをもらって、中身を行ごとのリストで返す
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

    basedir = os.path.dirname(os.path.abspath(__file__))

    # typ = [('てきすとふぁいる', '*.txt')]
    typ = [('', '*')]
    # kwargs['input_filepath'] = filedialog.askopenfilename(filetypes=typ, initialdir='.')
    kwargs['input_filepath'] = os.path.join(basedir, 'input.txt')

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
