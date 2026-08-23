from tree_sitter import Language, Parser
import tree_sitter_typescript

from retriever.parser.javascript_parser import (
    JavaScriptSymbolParser,
)

TS_LANGUAGE = Language(
    tree_sitter_typescript.language_typescript()
)

TSX_LANGUAGE = Language(
    tree_sitter_typescript.language_tsx()
)

class TypeScriptSymbolParser(
    JavaScriptSymbolParser
):
    def __init__(self):
        self.parser = Parser(
            TS_LANGUAGE
        )

class TSXSymbolParser(
    JavaScriptSymbolParser
):
    def __init__(self):
        self.parser = Parser(
            TSX_LANGUAGE
        )