import os
import pickle
import re
import typing

import chardet

import settings
from if_idf import TfIdfIndex


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
        if len(exclusions) == 0:
            return result
        # получаем set фалов, которые нужно исключить из result
        excluded_filenames_list = [set(exluded_result.entries.keys()) for exluded_result in exclusions]
        excluded_filenames = excluded_filenames_list[0].union(*excluded_filenames_list)

        # исключаем лишние файлы
        result = {fname: entries for (fname, entries) in result.entries.items() if fname not in excluded_filenames}
        return SearchResult(result)

    def __getitem__(self, filename):
        return self.entries[filename]

    def __setitem__(self, key, value):
        self.entries[key] = value


class FolderIndex:

    def __init__(self):
        """
        хранит 
        - word_entires: {слово: {файл: [вхождения]}}
        - encodings:    {файл: кодировка}
        - tf_idf_index: TfIdfIndex
        """
        self.word_entires: dict[str, dict[str, list[WordEntry]]] = {}
        self.encodings = {}
        self.tf_idf_index = TfIdfIndex()

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
        # todo может выделить это в отдельный класс
        # индексация кодировки
        if filepath not in folder_index.encodings:
            folder_index.encodings[filepath] = self.get_encoding(filepath)
        encoding = folder_index.encodings[filepath]

        # индексация вхождений и tf_idf
        with open(filepath, 'r', encoding=encoding) as f:
            total_char_count = 0
            for i, line in enumerate(f.readlines()):
                line = line.casefold()
                for match in re.finditer(settings.WORD_REGEX, line):
                    word = match.group()
                    folder_index.add(word, filepath,
                                     WordEntry(match.span()[0] + total_char_count, i + 1,
                                               match.span()[1] - match.span()[0]))
                    # может и это выделить отдельно
                    folder_index.tf_idf_index.add(word, filepath)
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

    def get_encoding(self, filepath: str) -> str:
        detector = chardet.UniversalDetector()
        with open(filepath, 'rb') as fh:
            for line in fh:
                detector.feed(line)
                if detector.done:
                    break
            detector.close()
        return detector.result['encoding']


class FolderIndexSaveloader:
    @classmethod
    def save(cls, filepath: str, folder_index: FolderIndex):
        with open(filepath, 'wb') as f:
            pickle.dump(folder_index, f)

    @classmethod
    def load(cls, filepath: str) -> FolderIndex:
        with open(filepath, 'rb') as f:
            index = pickle.load(f)
        return index
