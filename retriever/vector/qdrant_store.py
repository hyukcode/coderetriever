from qdrant_client import (
    QdrantClient,
    models,
)


COLLECTION_NAME = (
    "repo_symbols"
)


class QdrantStore:

    def __init__(
        self,
        url: str = (
            "http://localhost:6333"
        ),
    ):

        self.client = QdrantClient(
            url=url
        )

    def init_collection(
        self,
    ):

        if self.client.collection_exists(
            COLLECTION_NAME
        ):
            return

        self.client.create_collection(
            collection_name=(
                COLLECTION_NAME
            ),

            vectors_config={
                "dense": (
                    models.VectorParams(
                        size=768,
                        distance=(
                            models.Distance.COSINE
                        ),
                    )
                )
            },

            sparse_vectors_config={
                "sparse": (
                    models.SparseVectorParams(
                        modifier=(
                            models.Modifier.IDF
                        )
                    )
                )
            },
        )

    def upsert_symbol(
        self,
        symbol_id: int,
        repo_id: int,
        path: str,
        language: str,
        symbol_type: str,
        qualified_name: str,
        dense_vector,
        sparse_vector,
    ):

        point = models.PointStruct(
            id=symbol_id,

            vector={
                "dense": (
                    dense_vector.tolist()
                ),

                "sparse": (
                    models.SparseVector(
                        indices=(
                            sparse_vector.indices
                            .tolist()
                        ),

                        values=(
                            sparse_vector.values
                            .tolist()
                        ),
                    )
                ),
            },

            payload={
                "symbol_id": symbol_id,
                "repo_id": repo_id,
                "path": path,
                "language": language,

                "symbol_type": (
                    symbol_type
                ),

                "qualified_name": (
                    qualified_name
                ),
            },
        )

        self.client.upsert(
            collection_name=(
                COLLECTION_NAME
            ),

            points=[point],
        )

    def delete(
        self,
        ids: list[int],
    ):

        if not ids:
            return

        self.client.delete(
            collection_name=(
                COLLECTION_NAME
            ),

            points_selector=(
                models.PointIdsList(
                    points=ids
                )
            ),
        )