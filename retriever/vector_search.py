from qdrant_client import models

from retriever.embedding.service import EmbeddingService
from retriever.vector.qdrant_store import (
    COLLECTION_NAME,
    QdrantStore,
)


class VectorSearch:

    def __init__(
        self,
        store: QdrantStore,
        embedding: EmbeddingService,
    ):
        self.store = store
        self.embedding = embedding

    def search(
        self,
        repo_id: int,
        query: str,
        top_k: int = 20,
    ) -> list[tuple[int, float]]:

        query = query.strip()

        if not query:
            return []

        dense_vector = self.embedding.dense(
            [query]
        )[0]

        sparse_vector = self.embedding.sparse(
            [query]
        )[0]

        sparse_query = models.SparseVector(
            indices=sparse_vector.indices.tolist(),
            values=sparse_vector.values.tolist(),
        )

        repo_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="repo_id",
                    match=models.MatchValue(
                        value=repo_id
                    ),
                )
            ]
        )

        response = (
            self.store.client.query_points(
                collection_name=(
                    COLLECTION_NAME
                ),
                prefetch=[
                    models.Prefetch(
                        query=sparse_query,
                        using="sparse",
                        limit=max(
                            top_k * 3,
                            30,
                        ),
                    ),
                    models.Prefetch(
                        query=(
                            dense_vector.tolist()
                        ),
                        using="dense",
                        limit=max(
                            top_k * 3,
                            30,
                        ),
                    ),
                ],
                query=models.FusionQuery(
                    fusion=models.Fusion.RRF
                ),
                query_filter=repo_filter,
                limit=top_k,
                with_payload=True,
            )
        )

        results = []

        for point in response.points:
            payload = point.payload or {}

            symbol_id = payload.get(
                "symbol_id"
            )

            if symbol_id is None:
                symbol_id = point.id

            results.append(
                (
                    int(symbol_id),
                    float(point.score),
                )
            )

        return results