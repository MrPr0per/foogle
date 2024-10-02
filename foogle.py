import re

import colorama

import logic_tree
from folder_index import WordEntry, SearchResult, FolderIndex, FolderIndexer

colorama.init()


class ExpressionSearcher:
    def __init__(self, folder_index: FolderIndex):
        self.folder_index = folder_index

    def search_by_or_tree(self, or_tree: logic_tree.OrTree):
        results_list = [self.search_by_and_tree(and_tree) for and_tree in or_tree.and_trees]
        results = SearchResult.unite(results_list)
        return results

    def search_by_and_tree(self, and_tree: logic_tree.AndTree) -> SearchResult:
        results_list = [self.search_by_exclusion_tree(exclusion_tree) for exclusion_tree in and_tree.exclusion_trees]
        results = SearchResult.intersect(results_list)
        return results

    def search_by_exclusion_tree(self, exclusion_tree: logic_tree.ExclusionTree) -> SearchResult:
        results_list = [self.search_by_atom(atom) for atom in exclusion_tree.atoms]
        results = SearchResult.exclude(results_list[0], results_list[1:])
        return results

    def search_by_atom(self, atom: logic_tree.Atom):
        if isinstance(atom, logic_tree.WordAtom):
            return SearchResult(self.folder_index[atom.value])
        # if isinstance(atom, logic_tree.NotAtom):
        #     raise NotImplemented()
        if isinstance(atom, logic_tree.TreeAtom):
            atom: logic_tree.TreeAtom
            return self.search_by_or_tree(atom.value)
        raise AssertionError()


class Foogle:
    def __init__(self, folderpath: str = None, index: FolderIndex = None):
        none_args_count = (folderpath, index).count(None)
        if none_args_count != 1:
            raise Exception(f'Ровно один агрумент должен быть не None, а не {none_args_count}: {(folderpath, index)}')

        if folderpath is not None:
            folder_index = FolderIndexer().index_folder(folderpath)
        elif index is not None:
            folder_index = index
        else:
            raise AssertionError()

        self.folder_index = folder_index

    def search_expression(self, querry):
        expr = logic_tree.LogicTreeParser(querry).parse()
        result = ExpressionSearcher(self.folder_index).search_by_or_tree(expr)
        self.show_results(result)
        return result

    def show_results(self, search_result: SearchResult):
        for filepath, entries in search_result.entries.items():
            print(re.sub(r'([^/]+?)\.txt', rf'{colorama.Fore.CYAN}\1{colorama.Fore.RESET}.txt', filepath))
            for entry in entries:
                print(self.make_snippet(filepath, entry))
            print()

    def make_snippet(self, filepath, entry: WordEntry, radius=40):
        with open(filepath, encoding=self.folder_index.encodings[filepath]) as f:
            text = f.read()

        left_ellipsis = True
        left_border = entry.offset - radius
        if left_border <= 0:
            left_ellipsis = False
            left_border = 0

        right_ellipsis = True
        right_border = entry.offset + entry.length + radius
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
        for i in range(entry.offset + entry.length, right_border):
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
        snippet += text[entry.offset:entry.offset + entry.length]
        # snippet += colorama.Back.RESET
        snippet += colorama.Fore.RESET
        snippet += text[entry.offset + entry.length:right_border]
        if right_ellipsis: snippet += '...'

        return snippet


def main():
    foogle = Foogle('tests/files/wiki_test')
    # foogle.search_expression('частотность OR шифр')
    # foogle.search_expression('((шифр) OR (частотность))')
    # foogle.search_expression('((шифр) OR (частотность)) AND Википедия')
    # foogle.search_expression('(шифр OR частотность) AND она OR может')
    foogle.search_expression(r'частотность \ Ципфа \ слова')
    # foogle.search_expression('частотность AND слова OR шифр')
    # foogle.search_expression('шифр')
    # foogle.search_word('частотность')


if __name__ == '__main__':
    main()
