import settings
import tokenization


class Atom:
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f'{self.value}'


class WordAtom(Atom):
    def __init__(self, word: str):
        super().__init__(word)

    def __repr__(self):
        return f'{self.value}'


class TreeAtom(Atom):
    def __init__(self, tree: 'OrTree'):
        super().__init__(tree)

    def __repr__(self):
        return f'({self.value})'


class ExclusionTree:
    def __init__(self, atoms: list[Atom]):
        self.atoms = atoms

    def __repr__(self):
        return f' {settings.EXCLUSION_TERM} '.join([f'{a}' for a in self.atoms])


class AndTree:
    def __init__(self, exclusion_trees: list[ExclusionTree]):
        self.exclusion_trees = exclusion_trees

    def __repr__(self):
        return f' {settings.AND_TERM} '.join([f'{a}' for a in self.exclusion_trees])


class OrTree:
    def __init__(self, and_trees: list['AndTree']):
        self.and_trees = and_trees

    def __repr__(self):
        return f' {settings.OR_TERM} '.join([f'{a}' for a in self.and_trees])


class LogicTreeParser:

    def __init__(self, query):
        self.tokens = tokenization.Tokenizator(query).tokenize()
        self.cursor = 0

    def parse(self):
        return self.parse_only_one_tree()

    def parse_only_one_tree(self):
        tree = self.parse_or_tree()
        if self.cursor != len(self.tokens):
            raise ValueError('в запросе несколько выражений, а не одно')
        return tree

    def parse_or_tree(self) -> OrTree:
        # грамматика:
        # or_tree        := and_tree       (OR_TERM     and_tree      )*
        # and_tree       := exclusion_tree (AND_TERM    exclusion_tree)*
        # exclusion_tree := atom           (EXLUDE_TERM exlusion_tree )*
        # atom := word | '(' tree ')'

        # примечание: дерево не может быть пустым

        and_trees = [self.parse_and_tree()]
        while True:
            token = self.current_token()
            if isinstance(token, tokenization.Operator) and token.value == settings.OR_TERM:
                self.cursor += 1
                and_trees.append(self.parse_and_tree())
            else:
                break
        return OrTree(and_trees)

    def parse_and_tree(self) -> AndTree:
        exclusion_trees = [self.parse_exclusion_tree()]
        while True:
            token = self.current_token()
            if isinstance(token, tokenization.Operator) and token.value == settings.AND_TERM:
                self.cursor += 1
                exclusion_trees.append(self.parse_exclusion_tree())
            else:
                break

        return AndTree(exclusion_trees)

    def parse_exclusion_tree(self) -> ExclusionTree:
        atoms = [self.parse_atom()]
        while True:
            token = self.current_token()
            if isinstance(token, tokenization.Operator) and token.value == settings.EXCLUSION_TERM:
                self.cursor += 1
                atoms.append(self.parse_atom())
            else:
                break
        return ExclusionTree(atoms)

    def parse_atom(self) -> Atom:
        token = self.current_token()
        if token is None:
            raise ValueError(f'в {self.tokens} должен быть {self.cursor}-й токен, а там конец строки')
        if isinstance(token, tokenization.Word):
            token: tokenization.Word
            self.cursor += 1
            return WordAtom(token.word)
        if isinstance(token, tokenization.LeftParenthesis):
            token: tokenization.LeftParenthesis
            self.cursor += 1
            tree = self.parse_or_tree()

            end_token = self.current_token()
            if isinstance(end_token, tokenization.RightParenthesis):
                self.cursor += 1
                return TreeAtom(tree)
            else:
                raise ValueError(f'в {self.tokens} {self.cursor}-й токен должен быть ), а не {token}')
        raise AssertionError()

    def current_token(self):
        if self.cursor < len(self.tokens):
            return self.tokens[self.cursor]
        return None


def main():
    # tree = LogicTreeParser('яблоки AND (треугольники AND NOT NOT азаза)').parse_tree()
    tree = LogicTreeParser('a a').parse()
    print(tree)


if __name__ == '__main__':
    main()
