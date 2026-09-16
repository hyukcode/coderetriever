from sqlalchemy import select

from storage.models import (
    CodeEdgeModel,
    SymbolModel,
)


class GraphBuilder:

    def __init__(
        self,
        session,
    ):
        self.session = session

    def build_file_edges(
        self,
        repo_id: int,
        file_id: int,
        relations,
    ) -> None:

        symbols = (
            self._load_repo_symbols(
                repo_id
            )
        )

        by_qualified = {
            symbol.qualified_name: symbol
            for symbol in symbols
        }

        by_name: dict[
            str,
            list[SymbolModel],
        ] = {}

        for symbol in symbols:

            by_name.setdefault(
                symbol.name,
                [],
            ).append(
                symbol
            )

        for relation in relations:

            source_symbol_id = (
                self._resolve_source(
                    relation.source_symbol,
                    by_qualified,
                )
            )

            target_symbol_id = (
                self._resolve_target(
                    relation.target_name,
                    by_qualified,
                    by_name,
                )
            )

            edge = CodeEdgeModel(
                repo_id=repo_id,
                source_file_id=file_id,
                source_symbol_id=(
                    source_symbol_id
                ),
                target_symbol_id=(
                    target_symbol_id
                ),
                edge_type=(
                    relation.edge_type
                ),
                target_name=(
                    relation.target_name
                ),
                line=relation.line,
            )

            self.session.add(
                edge
            )

    def _resolve_source(
        self,
        source_name: str | None,
        by_qualified,
    ) -> int | None:

        if not source_name:
            return None

        symbol = by_qualified.get(
            source_name
        )

        if symbol is None:
            return None

        return symbol.id

    def _resolve_target(
        self,
        target_name: str,
        by_qualified,
        by_name,
    ) -> int | None:

        normalized = (
            self._normalize_target(
                target_name
            )
        )

        if not normalized:
            return None

        direct = by_qualified.get(
            normalized
        )

        if direct is not None:
            return direct.id

        simple_name = (
            normalized
            .split(".")[-1]
        )

        simple_name = (
            simple_name
            .split("::")[-1]
        )

        candidates = by_name.get(
            simple_name,
            [],
        )

        if len(candidates) == 1:
            return candidates[0].id

        qualified_candidates = [
            symbol
            for qualified, symbol
            in by_qualified.items()
            if qualified.endswith(
                f".{normalized}"
            )
        ]

        if len(
            qualified_candidates
        ) == 1:

            return (
                qualified_candidates[0]
                .id
            )

        return None

    def _normalize_target(
        self,
        target_name: str,
    ) -> str:

        value = target_name.strip()

        if not value:
            return ""

        value = value.rstrip(
            ";"
        )

        if value.endswith("()"):
            value = value[:-2]

        if "<" in value:

            base = value.split(
                "<",
                1,
            )[0]

            if base:
                value = base

        return value.strip()

    def _load_repo_symbols(
        self,
        repo_id: int,
    ) -> list[SymbolModel]:

        stmt = (
            select(
                SymbolModel
            )
            .where(
                SymbolModel.repo_id
                == repo_id
            )
        )

        return list(
            self.session.scalars(
                stmt
            )
        )