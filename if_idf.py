import math
import re

import settings


class TfIdfIndex:
    def __init__(self):
        """
        хранит:
        - files_count                                   - общее количество файлов в индексе
        - word_count_in_file: {filepath: {word: count}} - количество вхождений слова в файл 
        - filepaths_by_word: {word: {filepaths}}        - множество файлов с данным словом 
        """
        self.filepaths = set()
        self.word_count_in_file = {}
        self.filepaths_by_word = {}

    def add(self, word, filepath):
        self.filepaths.add(filepath)

        if filepath not in self.word_count_in_file:
            self.word_count_in_file[filepath] = {}
        if word not in self.word_count_in_file[filepath]:
            self.word_count_in_file[filepath][word] = 0
        self.word_count_in_file[filepath][word] += 1

        if word not in self.filepaths_by_word:
            self.filepaths_by_word[word] = set()
        self.filepaths_by_word[word].add(filepath)

    def get_odered_filepaths_with_tf_idf(self, querry: str, search_result) -> list[tuple[str, float]]:
        """
        :param querry:
        :param search_result: 
        :return: [(файл, его_tf_idf), ...]
        """
        words_list = self.get_words_list(querry)
        filepaths = list(search_result.entries.keys())
        filepaths_and_tf_idfs = [
            (
                filepath,
                self.get_tf_idf(words_list, filepath)
            )
            for filepath in filepaths]
        filepaths_and_tf_idfs.sort(key=lambda pair: pair[1], reverse=True)
        return filepaths_and_tf_idfs

    def get_tf_idf(self, words_list: list[str], filepath: str) -> float:
        score = 0
        for w in words_list:
            score += self.get_tf_idf_by_word(w, filepath)
        return score

    def get_tf_idf_by_word(self, word: str, filepath: str) -> float:
        if word not in self.filepaths_by_word:
            # слова нет в нашем индексе
            return 0

        if filepath in self.word_count_in_file and word in self.word_count_in_file[filepath]:
            tf = self.word_count_in_file[filepath][word]
        else:
            tf = 0
        n = len(self.filepaths)
        df = len(self.filepaths_by_word[word])
        score = tf * math.log(n / df)
        return score

    def get_words_list(self, querry: str):
        words = re.findall(settings.WORD_REGEX, querry)
        words = [w for w in words if w not in settings.LOGIC_TERMS]
        return words
