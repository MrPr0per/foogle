import re


class Token:
    def __init__(self):
        pass


class Operator(Token):
    OPERATORS = ['OR', 'AND', 'NOT']

    def __init__(self, value):
        super().__init__()
        self.value = value

    def __repr__(self):
        return self.value


class Parenthesis(Token):
    def __init__(self):
        super().__init__()


class LeftParenthesis(Parenthesis):
    def __init__(self):
        super().__init__()

    def __repr__(self):
        return '('


class RightParenthesis(Parenthesis):
    def __init__(self):
        super().__init__()

    def __repr__(self):
        return ')'


class Word(Token):
    def __init__(self, word: str):
        super().__init__()
        self.word = word

    def __repr__(self):
        return self.word


class Tokenizator:
    def __init__(self, query: str):
        self.query = query
        self.tokens: list[Token] = []
        self.cursor = 0

    def tokenize(self) -> list[Token]:
        self.skip_spaces()
        while self.cursor < len(self.query):
            success = (self.try_read_parenthesis() or
                       self.try_read_operator() or
                       self.try_read_word())
            if not success:
                raise Exception('не удалось считать токен')

            self.skip_spaces()

        return self.tokens

    def skip_spaces(self):
        while self.cursor < len(self.query) and self.query[self.cursor].isspace():
            self.cursor += 1

    def try_read_parenthesis(self):
        char = self.query[self.cursor]
        if char == '(':
            self.tokens.append(LeftParenthesis())
            self.cursor += 1
            return True
        if char == ')':
            self.tokens.append(RightParenthesis())
            self.cursor += 1
            return True
        return False

    def try_read_operator(self):
        for op in Operator.OPERATORS:
            if self.cursor + len(op) > len(self.query): continue
            op_in_query = self.query[self.cursor:self.cursor + len(op)]
            if op == op_in_query and (
                    self.cursor + len(op) == len(self.query) or self.query[self.cursor + len(op)].isspace()):
                self.tokens.append(Operator(op))
                self.cursor += len(op)
                return True
        return False

    def try_read_word(self):
        match = re.search(r'\w+', self.query[self.cursor:])
        if match is None:
            return False
        if match.span()[0] > 0: return False

        self.tokens.append(Word(match.group()))
        self.cursor += match.span()[1]
        return True


def main():
    r = Tokenizator('(a AND b) OR NOT NUT ()()())()))((()()(() NOTasdfsafda hfuiewfiwu()wjhfjeNOT').tokenize()
    print(r)


if __name__ == '__main__':
    main()
