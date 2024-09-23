import os
import re
import typing

import colorama

import logic_tree

colorama.init()


class WordEntry:
    """одно вхождение слова в файл"""

    def __init__(self, offset: int, line: int):
        self.offset = offset
        self.line = line


class WordEntries:
    """все вхождения слова в файл"""

    def __init__(self, entries: dict[str, list[WordEntry]] = None):
        """
        :param entries: {файл: [вхождения]}
        """
        if entries is None: entries = {}
        self.entries = entries

    @classmethod
    def intersect(cls, entries_list: list['WordEntries']) -> 'WordEntries':
        # if len(entries_list) == 0: return WordEntries()
        if len(entries_list) == 0: raise ValueError('перресечение пустого набора результатов')

        all_filenames = [set(entries.entries.keys()) for entries in entries_list]
        # Начинаем с самого маленького множества, чтобы ускорить пересечение
        common_filenames = min(all_filenames, key=len)
        # Пересекаем его с остальными множествами
        common_filenames = common_filenames.intersection(*all_filenames)

        intersection = {}
        for common_filename in common_filenames:
            common_word_entries: list[WordEntry] = []
            for entries in entries_list:
                if common_filename not in entries.entries: continue
                common_word_entries.extend(entries.entries[common_filename])
                # todo: пофиксить дублирование в запросах вида "кукуруза AND кукуруза"
            common_word_entries.sort(key=lambda entry: entry.offset)
            intersection[common_filename] = common_word_entries
        return WordEntries(intersection)

    @classmethod
    def unite(cls, entries_list: list['WordEntries']) -> 'WordEntries':
        if len(entries_list) == 0: return WordEntries()

        all_filenames = [set(entries.entries.keys()) for entries in entries_list]
        common_filenames = all_filenames[0].union(*all_filenames)

        union = {}
        for common_filename in common_filenames:
            common_word_entries: list[WordEntry] = []
            for entries in entries_list:
                if common_filename not in entries.entries: continue
                common_word_entries.extend(entries.entries[common_filename])
                # todo: пофиксить дублирование в запросах вида "кукуруза AND кукуруза"
            common_word_entries.sort(key=lambda entry: entry.offset)
            union[common_filename] = common_word_entries
        return WordEntries(union)

    def __getitem__(self, filename):
        return self.entries[filename]

    def __setitem__(self, key, value):
        self.entries[key] = value


class FolderIndex:
    def __init__(self):
        self.word_entires: dict[str, dict[str, list[WordEntry]]] = {}  # {слово: {файл: [вхождения]}} 

    def add(self, word, filepath, entry: WordEntry):
        if word not in self.word_entires:
            self.word_entires[word] = {}
        if filepath not in self.word_entires[word]:
            self.word_entires[word][filepath] = []
        self.word_entires[word][filepath].append(entry)

    def __getitem__(self, word: str):
        if word in self.word_entires:
            return self.word_entires[word]
        return {}


class FolderIndexer:
    def __init__(self):
        pass

    def index_folder(self, folderpath):
        folder_index = FolderIndex()
        for filepath in self.iter_filepaths(folderpath):
            self.index_file(folder_index, filepath)
        return folder_index

    def index_file(self, folder_index: FolderIndex, filepath: str):
        # todo: определять и сохранять кодировку
        encoding = 'utf8'
        with open(filepath, 'r', encoding=encoding) as f:
            total_char_count = 0
            for i, line in enumerate(f.readlines()):
                line = line.casefold()
                for match in re.finditer(r'\w+', line):
                    folder_index.add(match.group(), filepath,
                                     WordEntry(match.span()[0] + total_char_count, i + 1))
                total_char_count += len(line)

    def iter_filepaths(self, folderpath) -> typing.Generator[str, None, None]:
        """рекурсивно проходится по всем файлам в папке и ее подпапкках"""
        for item in os.listdir(folderpath):
            item_path = folderpath + '/' + item
            if not os.path.isdir(item_path):
                yield item_path
            else:
                for filepath in self.iter_filepaths(item_path):
                    yield filepath


class ExpressionSearcher:
    def __init__(self, folder_index: FolderIndex):
        self.folder_index = folder_index

    def search_by_or_tree(self, or_tree: logic_tree.Tree):
        results = [self.search_by_and_tree(and_tree) for and_tree in or_tree.and_trees]
        # todo объединяем
        return results[0]

    def search_by_and_tree(self, and_tree: logic_tree.AndTree) -> WordEntries:
        results_list = [self.search_by_atom(atom) for atom in and_tree.atoms]
        results = WordEntries.intersect(results_list)
        return results

    def search_by_atom(self, atom: logic_tree.Atom):
        if isinstance(atom, logic_tree.WordAtom):
            return WordEntries(self.folder_index[atom.value])
        if isinstance(atom, logic_tree.NotAtom):
            raise NotImplemented()
        if isinstance(atom, logic_tree.TreeAtom):
            atom: logic_tree.TreeAtom
            return self.search_by_or_tree(atom.value)
        raise AssertionError()


class Foogle:
    def __init__(self, folderpath):
        folder_index = FolderIndexer().index_folder(folderpath)
        self.folder_index = folder_index

    def search_expression(self, querry):
        expr = logic_tree.LogicTreeParser(querry).parse()
        result = ExpressionSearcher(self.folder_index).search_by_or_tree(expr)
        self.show_results()
        return result

    def search_word(self, word, is_show_results=True):
        word = word.casefold()
        entries_by_file = self.folder_index[word]

        if is_show_results:
            self.show_results(entries_by_file, word)

        return entries_by_file

    def show_results(self, entries_by_file, word):
        for filepath, entries in entries_by_file.items():
            print(re.sub(r'([^/]+?)\.txt', rf'{colorama.Fore.CYAN}\1{colorama.Fore.RESET}.txt', filepath))
            for entry in entries:
                print(self.make_snippet(filepath, entry, len(word)))
            print()

    def make_snippet(self, filepath, entry: WordEntry, word_len, radius=40):
        with open(filepath, encoding='utf8') as f:
            text = f.read()

        left_ellipsis = True
        left_border = entry.offset - radius
        if left_border <= 0:
            left_ellipsis = False
            left_border = 0

        right_ellipsis = True
        right_border = entry.offset + word_len + radius
        if right_border >= len(text):
            right_ellipsis = False
            right_border = len(text)

        # ищем конец прошлой строки
        for i in range(entry.offset - 1, left_border - 1, -1):
            if text[i] == '\n':
                left_border = i + 1
                left_ellipsis = False
                break

        # ищем конец этой строки
        for i in range(entry.offset + word_len, right_border):
            if text[i] == '\n':
                right_border = i
                right_ellipsis = False
                break

        snippet = ''
        snippet += colorama.Fore.LIGHTBLACK_EX
        snippet += str(entry.line).rjust(4, ' ') + '  '
        snippet += colorama.Fore.RESET
        if left_ellipsis: snippet += '...'
        snippet += text[left_border:entry.offset]
        # snippet += colorama.Fore.WHITE
        # snippet += colorama.Back.LIGHTGREEN_EX
        snippet += colorama.Fore.GREEN
        snippet += text[entry.offset:entry.offset + word_len]
        # snippet += colorama.Back.RESET
        snippet += colorama.Fore.RESET
        snippet += text[entry.offset + word_len:right_border]
        if right_ellipsis: snippet += '...'

        return snippet


def main():
    foogle = Foogle('tests/files/wiki_test')
    # foogle.search_expression('частотность AND но')
    foogle.search_word('частотность')


if __name__ == '__main__':
    main()
