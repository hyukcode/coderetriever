from retriever.parser.java_parser import (
    JavaSymbolParser,
)
from retriever.parser.python_parser import (
    PythonSymbolParser,
)

from retriever.parser.javascript_parser import (
    JavaScriptSymbolParser,
)
from retriever.parser.typescript_parser import (
    TypeScriptSymbolParser,
    TSXSymbolParser,
)

class ParserRegistry:
    def __init__(self):
        js_parser = JavaScriptSymbolParser()
        self.parsers = {
            "python": PythonSymbolParser(),
            "java": JavaSymbolParser(),
            "javascript": js_parser,
            "jsx": js_parser,
            "typescript": (
                TypeScriptSymbolParser()
            ),
            "tsx": TSXSymbolParser(),
        }

    def get(self, language: str):
        parser = self.parsers.get(language)
        if parser is None:
            raise ValueError(
                f"Unsupported language: {language}"
            )
        return parser

