from tree_sitter import Language, Parser
import tree_sitter_python
from retriever.parser.base import SymbolParser
from retriever.parser.models import Symbol
from retriever.scanner import SourceFile

PY_LANGUAGE = Language(
    tree_sitter_python.language()
)

class PythonSymbolParser(SymbolParser):
    def __init__(self):
        self.parser = Parser(PY_LANGUAGE)

    def parse(
        self,
        source_file: SourceFile,
    ) -> list[Symbol]:
        source_bytes = source_file.path.read_bytes()
        tree = self.parser.parse(source_bytes)
        symbols: list[Symbol] = []
        self._walk(
            node=tree.root_node,
            source_bytes=source_bytes,
            source_file=source_file,
            symbols=symbols,
            parent_symbol=None,
        )
        return symbols
    
    def _walk(
        self,
        node,
        source_bytes: bytes,
        source_file: SourceFile,
        symbols: list[Symbol],
        parent_symbol: str | None,
    ):
        current_parent = parent_symbol
        if node.type == "class_definition":
            symbol = self._parse_class(
                node,
                source_bytes,
                source_file,
            )
            symbols.append(symbol)
            current_parent = symbol.name
        elif node.type == "function_definition":
            symbol = self._parse_function(
                node,
                source_bytes,
                source_file,
                parent_symbol
            )
            symbols.append(symbol)
        
        for child in node.children:
            self._walk(
                node=child,
                source_bytes=source_bytes,
                source_file=source_file,
                symbols=symbols,
                parent_symbol=current_parent,
            )
    
    def _parse_class(
        self,
        node,
        source_bytes,
        source_file,
    ) -> Symbol:
        name_node = node.child_by_field_name("name")
        name = self._text(
            name_node,
            source_bytes,
        )
        return Symbol(
            name=name,
            qualified_name=name,
            symbol_type="class",
            path=source_file.relative_path,
            language="python",
            start_line=node.start_point.row+1,
            end_line=node.end_point.row+1,
            signature=self._first_line(
                node,
                source_bytes,
            ),
            code=self._text(
                node,
                source_bytes,
            ),
        )
    
    def _parse_function(
        self,
        node,
        source_bytes,
        source_file,
        parent_symbol,
    ) -> Symbol:
        name_node = node.child_by_field_name("name")
        name = self._text(
            name_node,
            source_bytes,
        )
        if parent_symbol:
            qualified_name=(
                f"{parent_symbol}.{name}"
            )
            symbol_type = "method"
        else:
            qualified_name = name
            symbol_type = "function"
        return Symbol(
            name=name,
            qualified_name=qualified_name,
            symbol_type=symbol_type,
            path=source_file.relative_path,
            language="python",
            start_line=node.start_point.row+1,
            end_line=node.end_point.row+1,
            signature=self._first_line(
                node,
                source_bytes,
            ),
            code=self._text(
                node,
                source_bytes
            )
        )
    
    def _text(
        self,
        node,
        source_bytes: bytes
    ) -> str:
        return source_bytes[
            node.start_byte:node.end_byte
        ].decode(
            "utf-8",
            errors="replace",
        )
    
    def _first_line(
        self,
        node,
        source_bytes,
    ) -> str:
        text = self._text(
            node,
            source_bytes
        )
        return text.splitlines()[0]
