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
        self.parser = Parser(
            PY_LANGUAGE
        )

    def parse(
        self,
        source_file: SourceFile,
    ) -> list[Symbol]:

        source_bytes = (
            source_file.path.read_bytes()
        )

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

        if node.type == "class_definition":

            symbol = self._parse_class(
                node,
                source_bytes,
                source_file,
                scope,
            )

            symbols.append(symbol)

            child_scope = (
                scope + [symbol.name]
            )

        elif node.type in {
            "function_definition",
            "async_function_definition",
        }:

            symbol = self._parse_function(
                node,
                source_bytes,
                source_file,
                scope,
            )

            if symbol is not None:

                symbols.append(symbol)

                # 支持 function 内嵌 function
                child_scope = (
                    scope + [symbol.name]
                )

        for child in node.children:

            self._walk(
                child,
                source_bytes,
                source_file,
                symbols,
                child_scope,
            )

    def _parse_class(
        self,
        node,
        source_bytes,
        source_file,
        scope,
    ):

        name_node = (
            node.child_by_field_name(
                "name"
            )
        )

        name = self._text(
            name_node,
            source_bytes,
        )

        qualified_name = ".".join(
            scope + [name]
        )

        return Symbol(
            name=name,
            qualified_name=qualified_name,
            symbol_type="class",

            path=(
                source_file.relative_path
            ),

            language="python",

            start_line=(
                node.start_point.row + 1
            ),

            end_line=(
                node.end_point.row + 1
            ),

            signature=self._signature(
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
        scope,
    ):

        name_node = (
            node.child_by_field_name(
                "name"
            )
        )

        if name_node is None:
            return None

        name = self._text(
            name_node,
            source_bytes,
        )

        qualified_name = ".".join(
            scope + [name]
        )

        # 在 class scope 下是 method
        if self._is_inside_class(
            scope
        ):
            symbol_type = "method"
        else:
            symbol_type = "function"

        return Symbol(
            name=name,

            qualified_name=(
                qualified_name
            ),

            symbol_type=symbol_type,

            path=(
                source_file.relative_path
            ),

            language="python",

            start_line=(
                node.start_point.row + 1
            ),

            end_line=(
                node.end_point.row + 1
            ),

            signature=self._signature(
                node,
                source_bytes,
            ),

            code=self._text(
                node,
                source_bytes,
            ),
        )

    def _is_inside_class(
        self,
        scope,
    ):
        # V1 暂时只根据 scope 判断。
        # 后续可升级为显式 ScopeFrame。
        return len(scope) > 0

    def _signature(
        self,
        node,
        source_bytes,
    ):

        body = (
            node.child_by_field_name(
                "body"
            )
        )

        if body is None:

            return self._text(
                node,
                source_bytes,
            ).splitlines()[0]

        return source_bytes[
            node.start_byte:
            body.start_byte
        ].decode(
            "utf-8",
            errors="replace",
        ).strip()

    def _text(
        self,
        node,
        source_bytes,
    ):

        if node is None:
            return ""

        return source_bytes[
            node.start_byte:
            node.end_byte
        ].decode(
            "utf-8",
            errors="replace",
        )