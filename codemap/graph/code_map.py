from sqlalchemy import or_, select

from retriever.storage.models import (
    CodeEdgeModel,
    FileModel,
    SymbolModel,
)


class CodeMapService:

    def __init__(
        self,
        session,
    ):
        self.session = session

    def get_code_map(
        self,
        symbol_id: int,
        depth: int = 1,
    ):

        if depth < 0:
            depth = 0

        root = self._load_symbol(
            symbol_id
        )

        if root is None:
            return None

        root_symbol = root[0]
        root_path = root[1]

        nodes = {
            root_symbol.id: (
                self._node(
                    root_symbol,
                    root_path,
                )
            )
        }

        visited = {
            root_symbol.id
        }

        frontier = {
            root_symbol.id
        }

        edges = []

        edge_keys = set()

        imports = (
            self._load_file_imports(
                root_symbol.file_id
            )
        )

        for edge in imports:

            self._append_edge(
                edge=edge,
                edges=edges,
                edge_keys=edge_keys,
            )

        for _ in range(depth):

            if not frontier:
                break

            graph_edges = (
                self._load_symbol_edges(
                    frontier
                )
            )

            next_frontier = set()

            neighbor_ids = set()

            for edge in graph_edges:

                self._append_edge(
                    edge=edge,
                    edges=edges,
                    edge_keys=edge_keys,
                )

                if (
                    edge.source_symbol_id
                    is not None
                ):
                    neighbor_ids.add(
                        edge.source_symbol_id
                    )

                if (
                    edge.target_symbol_id
                    is not None
                ):
                    neighbor_ids.add(
                        edge.target_symbol_id
                    )

            neighbor_ids -= visited

            loaded = (
                self._load_symbols(
                    neighbor_ids
                )
            )

            for (
                neighbor_id,
                row,
            ) in loaded.items():

                symbol = row[0]
                path = row[1]

                nodes[
                    neighbor_id
                ] = self._node(
                    symbol,
                    path,
                )

                visited.add(
                    neighbor_id
                )

                next_frontier.add(
                    neighbor_id
                )

            frontier = next_frontier

        return {
            "root": (
                root_symbol.id
            ),
            "nodes": list(
                nodes.values()
            ),
            "edges": edges,
        }

    def _append_edge(
        self,
        edge,
        edges,
        edge_keys,
    ) -> None:

        key = (
            edge.id
        )

        if key in edge_keys:
            return

        edge_keys.add(
            key
        )

        edges.append(
            {
                "edge_id": (
                    edge.id
                ),
                "type": (
                    edge.edge_type
                ),
                "source_file_id": (
                    edge.source_file_id
                ),
                "source_symbol_id": (
                    edge.source_symbol_id
                ),
                "target_symbol_id": (
                    edge.target_symbol_id
                ),
                "target_name": (
                    edge.target_name
                ),
                "line": (
                    edge.line
                ),
                "resolved": (
                    edge.target_symbol_id
                    is not None
                ),
            }
        )

    def _load_file_imports(
        self,
        file_id: int,
    ):

        stmt = (
            select(
                CodeEdgeModel
            )
            .where(
                CodeEdgeModel.source_file_id
                == file_id
            )
            .where(
                CodeEdgeModel.source_symbol_id
                .is_(None)
            )
            .where(
                CodeEdgeModel.edge_type
                == "IMPORTS"
            )
            .order_by(
                CodeEdgeModel.line
            )
        )

        return list(
            self.session.scalars(
                stmt
            )
        )

    def _load_symbol_edges(
        self,
        symbol_ids: set[int],
    ):

        if not symbol_ids:
            return []

        stmt = (
            select(
                CodeEdgeModel
            )
            .where(
                or_(
                    CodeEdgeModel.source_symbol_id.in_(
                        symbol_ids
                    ),
                    CodeEdgeModel.target_symbol_id.in_(
                        symbol_ids
                    ),
                )
            )
            .order_by(
                CodeEdgeModel.id
            )
        )

        return list(
            self.session.scalars(
                stmt
            )
        )

    def _load_symbol(
        self,
        symbol_id: int,
    ):

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

        return (
            self.session.execute(
                stmt
            ).first()
        )

    def _load_symbols(
        self,
        symbol_ids: set[int],
    ):

        if not symbol_ids:
            return {}

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
                SymbolModel.id.in_(
                    symbol_ids
                )
            )
        )

        rows = (
            self.session.execute(
                stmt
            ).all()
        )

        return {
            symbol.id: (
                symbol,
                path,
            )
            for symbol, path
            in rows
        }

    def _node(
        self,
        symbol: SymbolModel,
        path: str,
    ):

        return {
            "symbol_id": (
                symbol.id
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
        }