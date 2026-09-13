from tree_sitter import Language, Parser
import tree_sitter_python

from retriever.relation.models import Relation
from retriever.scanner import SourceFile


PYTHON_LANGUAGE = Language(
    tree_sitter_python.language()
)


class PythonRelationParser:

    def __init__(self):
        self.parser = Parser(
            PYTHON_LANGUAGE
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

        if node.type == "class_definition":

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

                qualified_name = (
                    self._qualified_name(
                        scope,
                        name,
                    )
                )

                child_scope = (
                    scope + [name]
                )

                superclasses = (
                    node.child_by_field_name(
                        "superclasses"
                    )
                )

                if superclasses is not None:

                    for child in (
                        superclasses.named_children
                    ):

                        target = self._text(
                            child,
                            source_bytes,
                        ).strip()

                        if not target:
                            continue

                        if child.type in {
                            "keyword_argument",
                            "list_splat",
                            "dictionary_splat",
                        }:
                            continue

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

        elif node.type == "function_definition":

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

        elif node.type in {
            "import_statement",
            "import_from_statement",
            "future_import_statement",
        }:

            target = self._import_target(
                node,
                source_bytes,
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

        elif node.type == "call":

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

    def _import_target(
        self,
        node,
        source_bytes: bytes,
    ) -> str:

        if node.type == "import_from_statement":

            module_node = (
                node.child_by_field_name(
                    "module_name"
                )
            )

            if module_node is not None:
                return self._text(
                    module_node,
                    source_bytes,
                ).strip()

        value = self._text(
            node,
            source_bytes,
        ).strip()

        if value.startswith("import "):
            return value[
                len("import "):
            ].strip()

        if value.startswith("from "):

            remaining = value[
                len("from "):
            ]

            if " import " in remaining:

                return remaining.split(
                    " import ",
                    1,
                )[0].strip()

        return value

    def _qualified_name(
        self,
        scope: list[str],
        name: str,
    ) -> str:

        return ".".join(
            scope + [name]
        )

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