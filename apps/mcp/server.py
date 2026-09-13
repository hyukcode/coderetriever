from sqlalchemy import select

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from codemap.graph.code_map import CodeMapService
from retriever.retriever import CodeRetriever
from storage.database import SessionLocal
from storage.models import (
    FileModel,
    SymbolModel,
)


mcp = MCPServer(
    "repo-retriever"
)


@mcp.tool(
    name="search_code",
    title="Search Repository Code",
    description=(
        "Search indexed repository code using symbol, "
        "sparse and semantic retrieval. "
        "Use this first when locating implementations, "
        "classes, methods, components, hooks or related code."
    ),
    structured_output=True,
)
def search_code(
    repo: str,
    query: str,
    top_k: int = 10,
) -> dict:

    repo = repo.strip()
    query = query.strip()

    if not repo:
        raise ToolError(
            "repo must not be empty"
        )

    if not query:
        raise ToolError(
            "query must not be empty"
        )

    top_k = max(
        1,
        min(
            top_k,
            50,
        ),
    )

    try:

        with SessionLocal() as session:

            retriever = CodeRetriever(
                session
            )

            results = (
                retriever.search_code(
                    repo=repo,
                    query=query,
                    top_k=top_k,
                )
            )

            return {
                "repo": repo,
                "query": query,
                "count": len(results),
                "results": [
                    {
                        "symbol_id": (
                            result.symbol_id
                        ),
                        "name": (
                            result.name
                        ),
                        "qualified_name": (
                            result.qualified_name
                        ),
                        "symbol_type": (
                            result.symbol_type
                        ),
                        "path": (
                            result.path
                        ),
                        "language": (
                            result.language
                        ),
                        "start_line": (
                            result.start_line
                        ),
                        "end_line": (
                            result.end_line
                        ),
                        "signature": (
                            result.signature
                        ),
                        "code": (
                            result.code
                        ),
                        "score": (
                            result.score
                        ),
                        "match_type": (
                            result.match_type
                        ),
                    }
                    for result
                    in results
                ],
            }

    except ToolError:
        raise

    except Exception as exc:

        raise ToolError(
            f"search_code failed: "
            f"{exc}"
        ) from exc


@mcp.tool(
    name="get_symbol",
    title="Get Repository Symbol",
    description=(
        "Get the full indexed source code and metadata "
        "for a symbol by symbol_id. "
        "Use this after search_code when the complete "
        "implementation of a specific symbol is needed."
    ),
    structured_output=True,
)
def get_symbol(
    symbol_id: int,
) -> dict:

    if symbol_id <= 0:
        raise ToolError(
            "symbol_id must be positive"
        )

    try:

        with SessionLocal() as session:

            stmt = (
                select(
                    SymbolModel,
                    FileModel.relative_path,
                )
                .join(
                    FileModel,
                    FileModel.id
                    == SymbolModel.file_id,
                )
                .where(
                    SymbolModel.id
                    == symbol_id
                )
                .limit(1)
            )

            row = (
                session.execute(
                    stmt
                ).first()
            )

            if row is None:
                raise ToolError(
                    f"symbol not found: "
                    f"{symbol_id}"
                )

            symbol = row[0]
            path = row[1]

            return {
                "symbol_id": (
                    symbol.id
                ),
                "repo_id": (
                    symbol.repo_id
                ),
                "file_id": (
                    symbol.file_id
                ),
                "name": (
                    symbol.name
                ),
                "qualified_name": (
                    symbol.qualified_name
                ),
                "symbol_type": (
                    symbol.symbol_type
                ),
                "language": (
                    symbol.language
                ),
                "path": path,
                "start_line": (
                    symbol.start_line
                ),
                "end_line": (
                    symbol.end_line
                ),
                "signature": (
                    symbol.signature
                ),
                "code": (
                    symbol.code
                ),
                "parent_symbol": (
                    symbol.parent_symbol
                ),
                "exported": (
                    symbol.exported
                ),
            }

    except ToolError:
        raise

    except Exception as exc:

        raise ToolError(
            f"get_symbol failed: "
            f"{exc}"
        ) from exc


@mcp.tool(
    name="get_code_map",
    title="Get Symbol Code Map",
    description=(
        "Get the local dependency graph around a symbol. "
        "Returns CALLS, IMPORTS, EXTENDS and IMPLEMENTS "
        "relationships together with nearby symbols. "
        "Use this after search_code to understand how "
        "a symbol connects to the surrounding code."
    ),
    structured_output=True,
)
def get_code_map(
    symbol_id: int,
    depth: int = 1,
) -> dict:

    if symbol_id <= 0:
        raise ToolError(
            "symbol_id must be positive"
        )

    depth = max(
        0,
        min(
            depth,
            3,
        ),
    )

    try:

        with SessionLocal() as session:

            service = CodeMapService(
                session
            )

            result = (
                service.get_code_map(
                    symbol_id=symbol_id,
                    depth=depth,
                )
            )

            if result is None:
                raise ToolError(
                    f"symbol not found: "
                    f"{symbol_id}"
                )

            return result

    except ToolError:
        raise

    except Exception as exc:

        raise ToolError(
            f"get_code_map failed: "
            f"{exc}"
        ) from exc


def main():
    mcp.run()


if __name__ == "__main__":
    main()