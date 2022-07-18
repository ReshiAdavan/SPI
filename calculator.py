"""
NOTES
- SPI: Simple Pascal Interpreter
- EOF (end-of-file) token is used to indicate that input has ended for lexical analysis

"""

# Token Types
INTEGER, PLUS, MINUS, DIVIDE, MULTIPLY, LEFT_PARENTHESIS, RIGHT_PARENTHESIS, EOF = (
    'INTEGER', 'PLUS', 'MINUS', 'DIVIDE', 'MULTIPLY', '(', ')', 'EOF'
)


class Token(object):
    def __init__(self, type, value):
        """
        - Token Types: INTEGER, PLUS, MINUS, DIVIDE, MULTIPLY, LEFT_PARENTHESIS, RIGHT_PARENTHESIS, EOF
        - Token Values: 0,1,2,3,4,5,6,7,8,9, '+', '-', '/', '*','(', ')' or None
        """
        self.type = type
        self.value = value

    def __str__(self):
        """
        - def __str__(self) is a string representation of the class def __init__(self, type, value)
        - Ex: Token(INTEGER, 5), TOKEN(MINUS, '-')
        """
        return 'Token({type}, {value})'.format(
            type=self.type,
            value=repr(self.value)  # returns string representation of the value passed to eval function by default
        )

    def __repr__(self):
        """returns string representation of the object"""
        return self.__str__()


class Lexer(object):
    def __init__(self, text):
        """
        - string input, e.g. "3 * 5", "12 / 3 * 4", etc
        - self.pos is an index into self.text
        """
        self.text = text
        self.pos = 0
        self.current_char = self.text[self.pos]

    def error(self):
        raise Exception('Invalid character')

    def advance(self):
        """Advance the `pos` pointer and set the `current_char` variable."""
        self.pos += 1
        if self.pos > len(self.text) - 1:
            self.current_char = None  # Indicates end of input
        else:
            self.current_char = self.text[self.pos]

    def skip_whitespace(self):
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def integer(self):
        """Return a (multi-digit) integer consumed from the input."""
        result = ''
        while self.current_char is not None and self.current_char.isdigit():
            result += self.current_char
            self.advance()
        return int(result)

    def get_next_token(self):
        """
        - Lexical Analyzer (aka a scanner or tokenizer)
        - Responsible for breaking input apart into tokens
        """
        while self.current_char is not None:
            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            if self.current_char.isdigit():
                return Token(INTEGER, self.integer())

            # For addition
            if self.current_char == '+':
                self.advance()
                return Token(PLUS, '+')

            # For subtraction
            if self.current_char == '-':
                self.advance()
                return Token(MINUS, '-')

            # For multiplication
            if self.current_char == '*':
                self.advance()
                return Token(MULTIPLY, '*')

            # For division
            if self.current_char == '/':
                self.advance()
                return Token(DIVIDE, '/')

            # Left Parenthesis
            if self.current_char == '(':
                self.advance()
                return Token(LEFT_PARENTHESIS, '(')

            # Right Parenthesis
            if self.current_char == ')':
                self.advance()
                return Token(RIGHT_PARENTHESIS, ')')

            self.error()

        return Token(EOF, None)


## PARSING ##

class AST(object):
    """Abstract Syntax Diagram Class"""
    pass


class BinaryOperation(AST):
    """Binary Operation between terms in the AST"""

    def __init__(self, left, operation, right):
        self.left = left
        self.token = self.operation = operation
        self.right = right


class UnaryOperation(AST):
    """Unary Operation between terms in the AST"""

    def __init__(self, operation, expr):
        self.token = self.operation = operation
        self.expr = expr


class Num(AST):
    """A representation of the number token created in the AST"""

    def __init__(self, token):
        self.token = token
        self.value = token.value


class Parser(object):
    def __init__(self, lexer):
        """set current token to the first token taken from the input"""
        self.lexer = lexer
        self.current_token = self.lexer.get_next_token()

    def error(self):
        raise Exception('Invalid syntax')

    def overwrite(self, token_type):
        """
        - compare the current token type with the passed token type and if they match then overwrite the current token
        and assign the next token to the self.current_token.
        - otherwise raise an exception.
        """

        if self.current_token.type == token_type:
            self.current_token = self.lexer.get_next_token()
        else:
            self.error()

    def factor(self):
        """factor : (PLUS | MINUS) factor | INTEGER | LEFT_PARENTHESIS expr RIGHT_PARENTHESIS"""
        token = self.current_token
        if token.type == PLUS:
            self.overwrite(PLUS)
            node = UnaryOperation(token, self.factor())
            return node

        elif token.type == MINUS:
            self.overwrite(MINUS)
            node = UnaryOperation(token, self.factor())
            return node

        elif token.type == INTEGER:
            self.overwrite(INTEGER)
            return Num(token)

        elif token.type == LEFT_PARENTHESIS:
            self.overwrite(LEFT_PARENTHESIS)
            node = self.expr()
            self.overwrite(RIGHT_PARENTHESIS)
            return node

    def term(self):
        """term : factor ((MUL | DIV) factor)*"""
        node = self.factor()

        while self.current_token.type in (MULTIPLY, DIVIDE):
            token = self.current_token
            if token.type == MULTIPLY:
                self.overwrite(MULTIPLY)

            if token.type == DIVIDE:
                self.overwrite(DIVIDE)

            node = BinaryOperation(left=node, operation=token, right=self.factor())

        return node

    def expr(self):
        """
        - Arithmetic expression parser / interpreter.

        $ INPUT
        calc>  14 + 2 * 3 - 6 / 2
        17
        $ END

        Syntax Diagram
        - expr   : term ((PLUS | MINUS) term)*
        - term   : factor ((MUL | DIV) factor)*
        - factor : INTEGER
        """
        node = self.term()

        while self.current_token.type in (PLUS, MINUS):
            token = self.current_token
            if token.type == PLUS:
                self.overwrite(PLUS)
            elif token.type == MINUS:
                self.overwrite(MINUS)

            node = BinaryOperation(left=node, operation=token, right=self.term())

        return node

    def parse(self):
        return self.expr()


## INTERPRETER ##

class NodeVisitor(object):
    def visit(self, node):
        """visiting each node and executing a certain method depending on the node properties"""
        method_name = 'visit_' + type(node).__name__
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        """if we cannot recognize the node"""
        raise Exception('No visit_{} method'.format(type(node).__name__))


class Interpreter(NodeVisitor):
    def __init__(self, parser):
        self.parser = parser

    def visit_BinaryOperation(self, node):
        """Executing binary operations"""
        if node.operation.type == PLUS:
            return self.visit(node.left) + self.visit(node.right)
        elif node.operation.type == MINUS:
            return self.visit(node.left) - self.visit(node.right)
        elif node.operation.type == MULTIPLY:
            return self.visit(node.left) * self.visit(node.right)
        elif node.operation.type == DIVIDE:
            return self.visit(node.left) / self.visit(node.right)

    def visit_UnaryOperation(self, node):
        operation = node.operation.type
        if operation == PLUS:
            return +self.visit(node.expr)
        elif operation == MINUS:
            return -self.visit(node.expr)

    def visit_Num(self, node):
        return node.value

    def interpret(self):
        tree = self.parser.parse()
        return self.visit(tree)


def main():
    while True:
        try:
            text = input('SPI> ')
        except EOFError:
            break
        if not text:
            continue

        lexer = Lexer(text)
        parser = Parser(lexer)
        interpreter = Interpreter(parser)
        result = interpreter.interpret()
        print(result)


if __name__ == '__main__':
    main()
