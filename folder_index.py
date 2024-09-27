import os
import re
import typing


class WordEntry:
    """одно вхождение одного слова в один файл"""

    def __init__(self, offset: int, line: int, length: int):
        self.offset = offset
        self.length = length
        self.line = line


class SearchResult:
    """хранит {файл: [вхождения]}"""

    def __init__(self, entries: dict[str, list[WordEntry]] = None):
        if entries is None: entries = {}
        self.entries = entries

    @classmethod
    def intersect(cls, entries_list: list['SearchResult']) -> 'SearchResult':
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
        return SearchResult(intersection)

    @classmethod
    def unite(cls, entries_list: list['SearchResult']) -> 'SearchResult':
        if len(entries_list) == 0: return SearchResult()

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
        return SearchResult(union)

    @classmethod
    def exclude(cls, result: 'SearchResult', exclusions: list['SearchResult']) -> 'SearchResult':
        # получаем set фалов, которые нужно исключить из result
        excluded_filenames_list = [set(exluded_result.entries.keys()) for exluded_result in exclusions]
        excluded_filenames = excluded_filenames_list[0].union(*excluded_filenames_list)

        # исключаем лишние файлы
        result = {filename: entries for (filename, entries) in result.entries.items() if filename not in excluded_filenames}
        return SearchResult(result)

    def __getitem__(self, filename):
        return self.entries[filename]

    def __setitem__(self, key, value):
        self.entries[key] = value


class FolderIndex:
    """хранит {слово: {файл: [вхождения]}}"""

    def __init__(self):
        self.word_entires: dict[str, dict[str, list[WordEntry]]] = {}

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
                                     WordEntry(match.span()[0] + total_char_count, i + 1,
                                               match.span()[1] - match.span()[0]))
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
