from codemap.relation.java_relation_parser import (
    JavaRelationParser,
)
from codemap.relation.javascript_relation_parser import (
    JavaScriptRelationParser,
)
from codemap.relation.python_relation_parser import (
    PythonRelationParser,
)
from codemap.relation.typescript_relation_parser import (
    TSXRelationParser,
    TypeScriptRelationParser,
)


class RelationParserRegistry:

    def __init__(self):

        javascript_parser = (
            JavaScriptRelationParser()
        )

        self.parsers = {
            "python": (
                PythonRelationParser()
            ),
            "java": (
                JavaRelationParser()
            ),
            "javascript": (
                javascript_parser
            ),
            "jsx": (
                javascript_parser
            ),
            "typescript": (
                TypeScriptRelationParser()
            ),
            "tsx": (
                TSXRelationParser()
            ),
        }

    def get(
        self,
        language: str,
    ):

        parser = self.parsers.get(
            language
        )

        if parser is None:
            raise ValueError(
                f"Unsupported language: "
                f"{language}"
            )

        return parser