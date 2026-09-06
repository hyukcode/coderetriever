from sqlalchemy import or_, select

from retriever.embedding.service import (
    EmbeddingService,
)
from retriever.retrieval.models import (
    SearchResult,
)
from retriever.retrieval.symbol_search import (
    SymbolSearch,
)
from retriever.retrieval.vector_search import (
    VectorSearch,
)
from retriever.storage.models import (
    FileModel,
    RepositoryModel,
    SymbolModel,
)
from retriever.vector.qdrant_store import (
    QdrantStore,
)


class CodeRetriever:

    def __init__(
        self,
        session,
    ):
        self.session = session

        self.symbol_search = SymbolSearch(
            session
        )

        self.qdrant_store = QdrantStore()

        self.embedding = EmbeddingService()

        self.vector_search = VectorSearch(
            store=self.qdrant_store,
            embedding=self.embedding,
        )

    def search_code(
        self,
        repo: str,
        query: str,
        top_k: int = 10,
    ) -> list[SearchResult]:

        query = query.strip()

        if not query:
            return []

        repo_model = self._find_repo(
            repo
        )

        if repo_model is None:
            return []

        candidate_limit = max(
            top_k * 3,
            30,
        )

        symbol_results = (
            self.symbol_search.search(
                repo=repo,
                query=query,
                top_k=candidate_limit,
            )
        )

        vector_results = (
            self.vector_search.search(
                repo_id=repo_model.id,
                query=query,
                top_k=candidate_limit,
            )
        )

        scores: dict[
            int,
            dict
        ] = {}

        for rank, result in enumerate(
            symbol_results
        ):
            entry = scores.setdefault(
                result.symbol_id,
                {
                    "symbol_rank": None,
                    "symbol_score": 0.0,
                    "vector_rank": None,
                    "vector_score": 0.0,
                },
            )

            entry["symbol_rank"] = rank

            entry["symbol_score"] = (
                float(result.score)
            )

        for rank, (
            symbol_id,
            vector_score,
        ) in enumerate(
            vector_results
        ):
            entry = scores.setdefault(
                symbol_id,
                {
                    "symbol_rank": None,
                    "symbol_score": 0.0,
                    "vector_rank": None,
                    "vector_score": 0.0,
                },
            )

            entry["vector_rank"] = rank

            entry["vector_score"] = (
                vector_score
            )

        if not scores:
            return []

        ranked = []

        for symbol_id, data in (
            scores.items()
        ):
            final_score = (
                self._fusion_score(
                    symbol_rank=(
                        data["symbol_rank"]
                    ),
                    symbol_score=(
                        data["symbol_score"]
                    ),
                    vector_rank=(
                        data["vector_rank"]
                    ),
                )
            )

            ranked.append(
                (
                    symbol_id,
                    final_score,
                    data,
                )
            )

        ranked.sort(
            key=lambda item: item[1],
            reverse=True,
        )

        ranked = ranked[
            :top_k
        ]

        symbol_ids = [
            symbol_id
            for symbol_id, _, _
            in ranked
        ]

        symbol_map = (
            self._load_symbols(
                symbol_ids
            )
        )

        results = []

        for (
            symbol_id,
            final_score,
            source_data,
        ) in ranked:

            loaded = symbol_map.get(
                symbol_id
            )

            if loaded is None:
                continue

            symbol, path = loaded

            match_type = (
                self._match_type(
                    source_data
                )
            )

            results.append(
                SearchResult(
                    symbol_id=symbol.id,
                    name=symbol.name,
                    qualified_name=(
                        symbol.qualified_name
                    ),
                    symbol_type=(
                        symbol.symbol_type
                    ),
                    path=path,
                    language=(
                        symbol.language
                    ),
                    start_line=(
                        symbol.start_line
                    ),
                    end_line=(
                        symbol.end_line
                    ),
                    signature=(
                        symbol.signature
                    ),
                    code=(
                        symbol.code
                    ),
                    score=final_score,
                    match_type=match_type,
                )
            )

        return results

    def _fusion_score(
        self,
        symbol_rank: int | None,
        symbol_score: float,
        vector_rank: int | None,
    ) -> float:

        score = 0.0

        if symbol_rank is not None:
            score += (
                2.0
                / (
                    60
                    + symbol_rank
                )
            )

        if vector_rank is not None:
            score += (
                1.0
                / (
                    60
                    + vector_rank
                )
            )

        if symbol_score >= 100:
            score += 0.1

        elif symbol_score >= 95:
            score += 0.08

        elif symbol_score >= 80:
            score += 0.05

        return score

    def _load_symbols(
        self,
        symbol_ids: list[int],
    ) -> dict[
        int,
        tuple[
            SymbolModel,
            str,
        ]
    ]:

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

        rows = self.session.execute(
            stmt
        ).all()

        return {
            symbol.id: (
                symbol,
                path,
            )
            for symbol, path
            in rows
        }

    def _match_type(
        self,
        source_data: dict,
    ) -> str:

        has_symbol = (
            source_data[
                "symbol_rank"
            ]
            is not None
        )

        has_vector = (
            source_data[
                "vector_rank"
            ]
            is not None
        )

        if (
            has_symbol
            and has_vector
        ):
            return "symbol+hybrid"

        if has_symbol:
            return "symbol"

        return "hybrid"

    def _find_repo(
        self,
        repo: str,
    ) -> RepositoryModel | None:

        stmt = (
            select(
                RepositoryModel
            )
            .where(
                or_(
                    RepositoryModel.name
                    == repo,
                    RepositoryModel.root_path
                    == repo,
                )
            )
            .limit(1)
        )

        return self.session.scalar(
            stmt
        )