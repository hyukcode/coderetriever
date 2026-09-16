from tree_sitter import Language, Parser
import tree_sitter_javascript

from codemap.relation.models import Relation
from retriever.scanner import SourceFile


JAVASCRIPT_LANGUAGE = Language(
    tree_sitter_javascript.language()
)


class JavaScriptRelationParser:

    def __init__(
        self,
        language=None,
    ):
        self.parser = Parser(
            language
            or JAVASCRIPT_LANGUAGE
        )

    def parse(
        self,
        source_file: SourceFile,
    ) -> list[Relation]:

        source_bytes = (
            source_file.path.read_bytes()
        )

        tree = self.parser.parse(
            source_bytes
        )

        relations: list[Relation] = []

        self._walk(
            node=tree.root_node,
            source_bytes=source_bytes,
            relations=relations,
            scope=[],
        )

        return relations

    def _walk(
        self,
        node,
        source_bytes: bytes,
        relations: list[Relation],
        scope: list[str],
    ) -> None:

        child_scope = scope

        if node.type in {
            "class_declaration",
            "abstract_class_declaration",
        }:

            name_node = (
                node.child_by_field_name(
                    "name"
                )
            )

            if name_node is not None:

                name = self._text(
                    name_node,
                    source_bytes,
                )

                qualified_name = ".".join(
                    scope + [name]
                )

                child_scope = (
                    scope + [name]
                )

                for child in (
                    node.named_children
                ):

                    if (
                        child.type
                        != "class_heritage"
                    ):
                        continue

                    target = self._class_heritage(
                        child,
                        source_bytes,
                    )

                    if target:

                        relations.append(
                            Relation(
                                edge_type="EXTENDS",
                                source_symbol=(
                                    qualified_name
                                ),
                                target_name=target,
                                line=(
                                    node.start_point.row
                                    + 1
                                ),
                            )
                        )

        elif node.type in {
            "function_declaration",
            "generator_function_declaration",
        }:

            name_node = (
                node.child_by_field_name(
                    "name"
                )
            )

            if name_node is not None:

                name = self._text(
                    name_node,
                    source_bytes,
                )

                child_scope = (
                    scope + [name]
                )

        elif node.type == "method_definition":

            name_node = (
                node.child_by_field_name(
                    "name"
                )
            )

            if name_node is not None:

                name = self._text(
                    name_node,
                    source_bytes,
                )

                child_scope = (
                    scope + [name]
                )

        elif node.type == "variable_declarator":

            name_node = (
                node.child_by_field_name(
                    "name"
                )
            )

            value_node = (
                node.child_by_field_name(
                    "value"
                )
            )

            if (
                name_node is not None
                and value_node is not None
                and value_node.type
                in {
                    "arrow_function",
                    "function_expression",
                    "generator_function",
                }
            ):

                name = self._text(
                    name_node,
                    source_bytes,
                )

                child_scope = (
                    scope + [name]
                )

        elif node.type == "import_statement":

            source_node = (
                node.child_by_field_name(
                    "source"
                )
            )

            target = self._text(
                source_node,
                source_bytes,
            ).strip()

            target = target.strip(
                "\"'"
            )

            if target:

                relations.append(
                    Relation(
                        edge_type="IMPORTS",
                        source_symbol=None,
                        target_name=target,
                        line=(
                            node.start_point.row
                            + 1
                        ),
                    )
                )

        elif node.type == "call_expression":

            function_node = (
                node.child_by_field_name(
                    "function"
                )
            )

            target = self._text(
                function_node,
                source_bytes,
            ).strip()

            if target:

                relations.append(
                    Relation(
                        edge_type="CALLS",
                        source_symbol=(
                            ".".join(scope)
                            if scope
                            else None
                        ),
                        target_name=target,
                        line=(
                            node.start_point.row
                            + 1
                        ),
                    )
                )

        for child in node.children:

            self._walk(
                node=child,
                source_bytes=source_bytes,
                relations=relations,
                scope=child_scope,
            )

    def _class_heritage(
        self,
        node,
        source_bytes: bytes,
    ) -> str:

        value = self._text(
            node,
            source_bytes,
        ).strip()

        if value.startswith(
            "extends "
        ):
            return value[
                len("extends "):
            ].strip()

        named_children = (
            node.named_children
        )

        if named_children:
            return self._text(
                named_children[0],
                source_bytes,
            ).strip()

        return value

    def _text(
        self,
        node,
        source_bytes: bytes,
    ) -> str:

        if node is None:
            return ""

        return source_bytes[
            node.start_byte:
            node.end_byte
        ].decode(
            "utf-8",
            errors="replace",
        )