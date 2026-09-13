from tree_sitter import Language
import tree_sitter_typescript

from retriever.relation.javascript_relation_parser import (
    JavaScriptRelationParser,
)


TYPESCRIPT_LANGUAGE = Language(
    tree_sitter_typescript.language_typescript()
)

TSX_LANGUAGE = Language(
    tree_sitter_typescript.language_tsx()
)


class TypeScriptRelationParser(
    JavaScriptRelationParser
):

    def __init__(self):
        super().__init__(
            language=TYPESCRIPT_LANGUAGE
        )


class TSXRelationParser(
    JavaScriptRelationParser
):

    def __init__(self):
        super().__init__(
            language=TSX_LANGUAGE
        )