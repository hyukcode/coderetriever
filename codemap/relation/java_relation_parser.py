from tree_sitter import Language, Parser
import tree_sitter_java

from codemap.relation.models import Relation
from retriever.scanner import SourceFile


JAVA_LANGUAGE = Language(
    tree_sitter_java.language()
)


class JavaRelationParser:

    TYPE_NODES = {
        "class_declaration",
        "interface_declaration",
        "record_declaration",
        "enum_declaration",
    }

    def __init__(self):
        self.parser = Parser(
            JAVA_LANGUAGE
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

        if node.type in self.TYPE_NODES:

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

                    if child.type == "superclass":

                        targets = (
                            self._extract_types(
                                child,
                                source_bytes,
                            )
                        )

                        for target in targets:

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

                    elif (
                        child.type
                        == "super_interfaces"
                    ):

                        targets = (
                            self._extract_types(
                                child,
                                source_bytes,
                            )
                        )

                        for target in targets:

                            relations.append(
                                Relation(
                                    edge_type="IMPLEMENTS",
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

                    elif (
                        child.type
                        == "extends_interfaces"
                    ):

                        targets = (
                            self._extract_types(
                                child,
                                source_bytes,
                            )
                        )

                        for target in targets:

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
            "method_declaration",
            "constructor_declaration",
            "compact_constructor_declaration",
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

        elif node.type == "import_declaration":

            target = self._text(
                node,
                source_bytes,
            ).strip()

            target = target.removeprefix(
                "import "
            ).strip()

            target = target.removeprefix(
                "static "
            ).strip()

            target = target.rstrip(
                ";"
            ).strip()

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

        elif node.type == "method_invocation":

            name_node = (
                node.child_by_field_name(
                    "name"
                )
            )

            object_node = (
                node.child_by_field_name(
                    "object"
                )
            )

            name = self._text(
                name_node,
                source_bytes,
            ).strip()

            obj = self._text(
                object_node,
                source_bytes,
            ).strip()

            if obj and name:
                target = (
                    f"{obj}.{name}"
                )
            else:
                target = name

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

    def _extract_types(
        self,
        node,
        source_bytes: bytes,
    ) -> list[str]:

        result: list[str] = []

        self._collect_type_nodes(
            node,
            source_bytes,
            result,
        )

        if result:
            return result

        value = self._text(
            node,
            source_bytes,
        ).strip()

        for prefix in [
            "extends ",
            "implements ",
        ]:
            if value.startswith(prefix):
                value = value[
                    len(prefix):
                ].strip()

        return [
            item.strip()
            for item in value.split(",")
            if item.strip()
        ]

    def _collect_type_nodes(
        self,
        node,
        source_bytes: bytes,
        result: list[str],
    ) -> None:

        if node.type in {
            "type_identifier",
            "scoped_type_identifier",
            "generic_type",
        }:

            parent = node.parent

            if (
                parent is not None
                and parent.type
                == "generic_type"
                and node.type
                != "generic_type"
            ):
                return

            value = self._text(
                node,
                source_bytes,
            ).strip()

            if value:
                result.append(
                    value
                )

            return

        for child in (
            node.named_children
        ):

            self._collect_type_nodes(
                child,
                source_bytes,
                result,
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