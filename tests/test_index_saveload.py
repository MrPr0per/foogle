from unittest import TestCase
from folder_index import FolderIndexer, FolderIndexSaveloader
from foogle import Foogle
from tests.test_encodings import TestFolderIndexer


class TestFolderIndexSaveloader(TestCase):
    def test(self):
        path = 'files/_indexes/saveload_test.txt'
        index = FolderIndexer().index_folder('files/encoding_test')
        FolderIndexSaveloader.save(path, index)
        index = FolderIndexSaveloader.load(path)
        TestFolderIndexer().test_foogle(Foogle(index=index))
