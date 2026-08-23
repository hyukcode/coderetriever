from tree_sitter import Language, Parser
import tree_sitter_java

from retriever.parser.base import SymbolParser
from retriever.parser.models import Symbol
from retriever.scanner import SourceFile

JAVA_LANGUAGE = Language(
    tree_sitter_java.language()
)

class JavaSymbolParser(SymbolParser):
    def __init__(self):
        self.parser = Parser(JAVA_LANGUAGE)

    def parse(
        self,
        source_file=SourceFile
    ) -> list[Symbol]:
        source_bytes = source_file.path.read_bytes()
        tree = self.parser.parse(source_bytes)
        symbols: list[Symbol] = []
        self._walk(
            tree.root_node,
            source_bytes,
            source_file,
            symbols,
            None,
        )

        return symbols
    
    def _walk(
        self,
        node,
        source_bytes,
        source_file,
        symbols,
        parent_symbol,
    ):
        current_parent = parent_symbol
        if node.type in {
            "class_declaration",
            "interface_declaration",
        }:
            symbol = self._parse_class(
                node,
                source_bytes,
                source_file,
            )
            symbols.append(symbol)
            current_parent = symbol.name
        elif node.type in {
            "method_declaration",
            "constructor_declaration",
        }:
            symbol = self._parse_function(
                node,
                source_bytes,
                source_file,
                parent_symbol,
            )
            symbols.append(symbol)

        for child in node.children:
            self._walk(
                child,
                source_bytes,
                source_file,
                symbols,
                current_parent
            )
    
    def _parse_class(
        self,
        node,
        source_bytes,
        source_file,
    ):
        name_node = node.child_by_field_name("name")
        name = self._text(
            name_node,
            source_bytes,
        )
        symbol_type = (
            "interface"
            if node.type == "interface_declaration"
            else "class"
        )

        return Symbol(
            name=name,
            qualified_name=name,
            symbol_type=symbol_type,
            path=source_file.relative_path,
            language="java",
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
        qualified_name = (
            f"{parent_symbol}.{name}"
            if parent_symbol
            else name
        )
        return Symbol(
            name=name,
            qualified_name=qualified_name,
            symbol_type=(
                "constructor"
                if node.type
                == "constructor_declaration"
                else "method"
            ),
            path=source_file.relative_path,
            language="java",
            start_line=node.start_point.row+1,
            end_line=node.end_point.row+1,
            signature=self._get_signature(
                node,
                source_bytes,
            ),
            code=self._text(
                node,
                source_bytes,
            ),
        )
    
    def _get_signature(
        self,
        node,
        source_bytes,
    ) -> str:
        body=node.child_by_field_name("body")
        if body is None:
            return self._first_line(
                node,
                source_bytes,
            )
        return source_bytes[
            node.start_byte:node.end_byte
        ].decode(
            "utf-8",
            errors="replace",
        ).strip()

    def _text(
        self,
        node,
        source_bytes,
    ):
        return source_bytes[
            node.start_byte:node.end_byte
        ].decode(
            "utf-8",
            errors="replace",
        )
    
    def _first_line(self, node, source_bytes):
        return self._text(
            node,
            source_bytes
        ).splitlines()[0]



