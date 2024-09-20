import tokenization


class Atom:
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f'{self.value}'


class NotAtom(Atom):
    def __init__(self, atom: Atom):
        super().__init__(atom)

    def __repr__(self):
        return f'NOT {self.value}'


class WordAtom(Atom):
    def __init__(self, word: str):
        super().__init__(word)

    def __repr__(self):
        return f'{self.value}'


class TreeAtom(Atom):
    def __init__(self, tree: 'Tree'):
        super().__init__(tree)

    def __repr__(self):
        return f'({self.value})'


class AndTree:
    def __init__(self, atoms: list[Atom]):
        self.atoms = atoms

    def __repr__(self):
        # if len(self.atoms) == 1: return str(self.atoms[0])
        # return ' AND '.join([f'({a})' for a in self.atoms])
        return ' AND '.join([f'{a}' for a in self.atoms])


class Tree:
    def __init__(self, and_trees: list[AndTree]):
        self.and_trees = and_trees

    def __repr__(self):
        # if len(self.and_trees) == 1: return str(self.and_trees[0])
        # return ' OR '.join([f'({a})' for a in self.and_trees])
        return ' OR '.join([f'{a}' for a in self.and_trees])


class LogicTreeParser:

    def __init__(self, query):
        self.tokens = tokenization.Tokenizator(query).tokenize()
        self.cursor = 0

    def parse(self):
        return self.parse_only_one_tree()

    def parse_only_one_tree(self):
        tree = self.parse_tree()
        if self.cursor != len(self.tokens):
            raise ValueError('в запросе несколько выражений, а не одно')
        return tree

    def parse_tree(self) -> Tree:
        # грамматика:
        # tree := or_tree 

        # or_tree := and_tree ('OR' and_tree)*
        # and_tree := atom ('AND' atom)*
        # atom := word | '(' tree ')' | 'NOT' atom

        # привечание: дерево не может быть пустым

        and_trees = [self.parse_and_tree()]
        while True:
            token = self.current_token()
            if isinstance(token, tokenization.Operator) and token.value == 'OR':
                self.cursor += 1
                and_trees.append(self.parse_and_tree())
            else:
                break
            # elif self.current_token() is None:
            #     break
            # else:
            #     raise ValueError(
            #         f'в {self.tokens} {self.cursor}-й токен должен быть OR или конец строки, а не {token}')
        return Tree(and_trees)

    def parse_and_tree(self) -> AndTree:
        atoms = [self.parse_atom()]
        while True:
            token = self.current_token()
            if isinstance(token, tokenization.Operator) and token.value == 'AND':
                self.cursor += 1
                atoms.append(self.parse_atom())
            else:
                break
            # else:
            #     raise ValueError(
            #         f'в {self.tokens} {self.cursor}-й токен должен быть AND или конец строки, а не {token}')
        return AndTree(atoms)

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
            tree = self.parse_tree()

            end_token = self.current_token()
            if isinstance(end_token, tokenization.RightParenthesis):
                self.cursor += 1
                return TreeAtom(tree)
            else:
                raise ValueError(f'в {self.tokens} {self.cursor}-й токен должен быть ), а не {token}')
        if isinstance(token, tokenization.Operator) and token.value == 'NOT':
            self.cursor += 1
            return NotAtom(self.parse_atom())
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
