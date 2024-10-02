from unittest import TestCase
from folder_index import FolderIndexer
from foogle import Foogle


class TestFolderIndexer(TestCase):
    def test_get_encoding(self):
        indexer = FolderIndexer()
        # self.assertEqual(indexer.get_encoding('files/encoding_test/ansi.txt'), 'ansi')
        self.assertEqual(indexer.get_encoding('files/encoding_test/cp1251.txt'), 'windows-1251')
        self.assertEqual(indexer.get_encoding('files/encoding_test/utf8.txt'), 'utf-8')
        self.assertEqual(indexer.get_encoding('files/encoding_test/utf16LE.txt'), 'UTF-16')

    def test_foogle(self, foogle=None):
        if foogle is None:
            foogle = Foogle('files/encoding_test')
        result = foogle.search_expression('текст')
        self.assertEqual(len(result.entries), 4)
        filename_and_ofset = []
        for filename, entr in result.entries.items():
            self.assertEqual(len(entr), 1)
            filename_and_ofset.append((filename, entr[0].offset))
        filename_and_ofset.sort()
        self.assertEqual(filename_and_ofset[0], ('files/encoding_test/ansi.txt', 0))
        self.assertEqual(filename_and_ofset[1], ('files/encoding_test/cp1251.txt', 0))
        self.assertEqual(filename_and_ofset[2], ('files/encoding_test/utf16LE.txt', 0))
        self.assertEqual(filename_and_ofset[3], ('files/encoding_test/utf8.txt', 0))
