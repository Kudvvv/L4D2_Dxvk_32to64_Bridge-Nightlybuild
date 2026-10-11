# SPDX-License-Identifier: MIT
"""Extract complete native fixture functions, including function-try handlers."""
import re


def _block_end(text, brace):
    # Ignore literals and comments: braces in diagnostic strings are not code.
    tokens = re.compile(r'//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|[{}]', re.S)
    depth = 0
    for token in tokens.finditer(text, brace):
        if token.group() == "{":
            depth += 1
        elif token.group() == "}":
            depth -= 1
            if depth == 0:
                return token.end()
    raise ValueError("Unclosed production function")


def function_bounds(text, signature):
    if text.count(signature) != 1:
        raise ValueError(f"Expected one function: {signature}")
    start = text.index(signature)
    brace = text.index("{", start)
    body_end = end = _block_end(text, brace)
    if re.search(r"\btry\s*$", text[start:brace]):
        handlers = 0
        while (match := re.match(r"\s*catch\s*\([^)]*\)\s*\{", text[end:])):
            end = _block_end(text, end + match.end() - 1)
            handlers += 1
        if not handlers:
            raise ValueError(f"Function-try handler missing: {signature}")
    return start, brace, body_end, end


def function(text, signature):
    start, _, _, end = function_bounds(text, signature)
    return text[start:end] + "\n"
