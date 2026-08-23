from tree_sitter import Language, Parser
import tree_sitter_javascript

from retriever.parser.base import SymbolParser
from retriever.parser.models import Symbol
from retriever.scanner import SourceFile

JS_LANGUAGE = Language(
    tree_sitter_javascript.language()
)

class JavaScriptSymbolParser(SymbolParser):

    def __init__(self):
        self.parser = Parser(JS_LANGUAGE)
    
    def parse(
        self,
        source_file: SourceFile,
    ) -> list[Symbol]:
        source_bytes = source_file.path.read_bytes()
        tree = self.parser.parse(
            source_bytes
        )
        symbols: list[Symbol] = []

        self._walk(
            node=tree.root_node,
            source_bytes=source_bytes,
            source_file=source_file,
            symbols=symbols,
            scope=[],
        )
        return symbols
    
    def _walk(
        self,
        node,
        source_bytes,
        source_file,
        symbols,
        scope,
    ):
        child_scope = scope
        if node.type == "class_declaration":
            symbol = self._parse_class(
                node,
                source_bytes,
                source_file,
                scope,
            )
            symbols.append(symbol)
            child_scope=scope+[
                symbol.name
            ]
        elif node.type == "function_declaration":
            symbol = self._parse_function(
                node,
                source_bytes,
                source_file,
                scope,
            )
            symbols.append(symbol)
        elif node.type == "variable_declarator":
            symbol = self._parse_variable_function(
                node,
                source_bytes,
                source_file,
                scope,
            )
            if symbol:
                symbols.append(symbol)
        elif node.type == "method_declaration":
            symbol = self._parse_variable_function(
                node,
                source_bytes,
                source_file,
                scope,
            )
            if symbol:
                symbols.append(symbol)
        for child in node.children:
            self._walk(
                node=child,
                source_bytes=source_bytes,
                source_file=source_file,
                symbols=symbols,
                scope=child_scope,
            )
        
    
    def _parse_class(
        self,
        node,
        source_bytes,
        source_file,
        scope,
    ):
        name_node=node.child_by_field_name("name")
        name=self._text(
            name_node,
            source_bytes,
        )
        qualified_name=".".join(
            scope+[name]
        )
        return Symbol(
            name=name,
            qualified_name=qualified_name,
            symbol_type="class",
            path=source_file.relative_path,
            language=source_file.language,
            start_line=node.start_point.row+1,
            end_line=node.end_point.row+1,
            signature=self._signature(
                node,
                source_bytes,
            ),
            code=self._text(
                node,
                source_bytes,
            )
        )

    def _parse_function(
        self,
        node,
        source_bytes,
        source_file,
        scope,
    ):
        name_node=node.child_by_field_name("name")
        if name_node is None:
            return None
        name=self._text(
            name_node,
            source_bytes,
        )
        qualified_name=".".join(
            scope+[name]
        )
        symbol_type=(
            self._infer_function_type(name)
        )
        return Symbol(
            name=name,
            qualified_name=qualified_name,
            symbol_type=symbol_type,
            path=source_file.relative_path,
            language=source_file.language,
            start_line=node.start_point.row+1,
            end_line=node.end_point.row+1,
            signature=self._signature(
                node,
                source_bytes,
            ),
            code=self._text(
                node,
                source_bytes,
            ),
        )
    
    def _infer_function_type(
        self,
        name: str,
    ) -> str:
        if name.startswith("use"):
            return "hook"
        if name[:1].isupper():
            return "component"
        return "function"

    def _parse_variable_function(
        self,
        node,
        source_bytes,
        source_file,
        scope,
    ):
        name_node=node.child_by_field_name("name")
        value_node=node.child_by_field_name("value")
        if (name_node is None or value_node is None):
            return None
        if value_node.type not in {
            "arrow_function",
            "function_expression",
        }:
            return None
        name=self._text(
            name_node,
            source_bytes,
        )
        qualified_name=".".join(
            scope+[name]
        )

        symbol_type=self._infer_function_type(name)

        return Symbol(
            name=name,
            qualified_name=qualified_name,
            symbol_type=symbol_type,
            path=source_file.relative_path,
            language=source_file.language,
            start_line=node.start_point.row+1,
            end_line=node.end_point.row+1,
            signature=self._variable_signature(
                node,
                source_bytes,
            ),
            code=self._text(
                node,
                source_bytes,
            )
        )
    
    def _parse_method(
        self,
        node,
        source_bytes,
        source_file,
        scope,
    ):
        name_node=node.child_by_field_name("name")
        if name_node is None:
            return None
        name=self._text(
            name_node,
            source_bytes,
        )
        qualified_name=".".join(
            scope+[name]
        )
        return Symbol(
            name=name,
            qualified_name=qualified_name,
            symbol_type="method",
            path=source_file.relative_path,
            language=source_file.language,
            start_line=node.start_point.row+1,
            end_line=node.end_point.row+1,
            signature=self._signature(
                node,
                source_bytes,
            ),
            code=self._text(
                node,
                source_bytes,
            )
        )
    
    def _text(
        self,
        node,
        source_bytes,
    ) -> str:
        return source_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="replace")
    
    def _signature(
        self,
        node,
        source_bytes,
    ) -> str:
        body=node.child_by_field_name("body")
        if body is None:
            return self._text(
                node,
                source_bytes,
            ).splitlines()[0]
        
        return source_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="replace").strip()
    
    def _variable_signature(
        self,
        node,
        source_bytes,
    ) -> str:
        text=self._text(
            node,
            source_bytes,
        )
        first_line=text.splitlines()[0]
        return first_line
    


        



