from dataclasses import dataclass

from tree_sitter import (
    Language,
    Parser,
)

import tree_sitter_java

from retriever.parser.base import (
    SymbolParser,
)
from retriever.parser.models import (
    Symbol,
)
from retriever.scanner import (
    SourceFile,
)


JAVA_LANGUAGE = Language(
    tree_sitter_java.language()
)


@dataclass
class ScopeFrame:
    name: str
    symbol_type: str


class JavaSymbolParser(
    SymbolParser
):

    CLASS_TYPES = {
        "class_declaration": "class",
        "interface_declaration": "interface",
        "enum_declaration": "enum",
        "record_declaration": "record",
    }

    def __init__(self):

        self.parser = Parser(
            JAVA_LANGUAGE
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

        symbols = []

        self._walk(
            tree.root_node,
            source_bytes,
            source_file,
            symbols,
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

        if node.type in self.CLASS_TYPES:

            symbol = (
                self._parse_type(
                    node,
                    source_bytes,
                    source_file,
                    scope,
                )
            )

            if symbol:

                symbols.append(symbol)

                child_scope = (
                    scope
                    + [
                        ScopeFrame(
                            name=symbol.name,
                            symbol_type=(
                                symbol.symbol_type
                            ),
                        )
                    ]
                )

        elif node.type == (
            "method_declaration"
        ):

            symbol = (
                self._parse_method(
                    node,
                    source_bytes,
                    source_file,
                    scope,
                )
            )

            if symbol:
                symbols.append(symbol)

        elif node.type == (
            "constructor_declaration"
        ):

            symbol = (
                self._parse_constructor(
                    node,
                    source_bytes,
                    source_file,
                    scope,
                )
            )

            if symbol:
                symbols.append(symbol)

        for child in node.children:

            self._walk(
                child,
                source_bytes,
                source_file,
                symbols,
                child_scope,
            )

    def _parse_type(
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

        qualified_name = (
            self._qualified_name(
                scope,
                name,
            )
        )

        return Symbol(
            name=name,

            qualified_name=(
                qualified_name
            ),

            symbol_type=(
                self.CLASS_TYPES[
                    node.type
                ]
            ),

            path=(
                source_file.relative_path
            ),

            language="java",

            start_line=(
                node.start_point.row + 1
            ),

            end_line=(
                node.end_point.row + 1
            ),

            signature=(
                self._signature(
                    node,
                    source_bytes,
                )
            ),

            code=self._text(
                node,
                source_bytes,
            ),
        )

    def _parse_method(
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

        return Symbol(
            name=name,

            qualified_name=(
                self._qualified_name(
                    scope,
                    name,
                )
            ),

            symbol_type="method",

            path=(
                source_file.relative_path
            ),

            language="java",

            start_line=(
                node.start_point.row + 1
            ),

            end_line=(
                node.end_point.row + 1
            ),

            signature=(
                self._signature(
                    node,
                    source_bytes,
                )
            ),

            code=self._text(
                node,
                source_bytes,
            ),
        )

    def _parse_method(
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

        return Symbol(
            name=name,

            qualified_name=(
                self._qualified_name(
                    scope,
                    name,
                )
            ),

            symbol_type="method",

            path=(
                source_file.relative_path
            ),

            language="java",

            start_line=(
                node.start_point.row + 1
            ),

            end_line=(
                node.end_point.row + 1
            ),

            signature=(
                self._signature(
                    node,
                    source_bytes,
                )
            ),

            code=self._text(
                node,
                source_bytes,
            ),
        )

    def _qualified_name(
        self,
        scope,
        name,
    ):

        names = [
            frame.name
            for frame in scope
        ]

        names.append(name)

        return ".".join(names)

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