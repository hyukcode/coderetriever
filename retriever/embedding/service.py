from fastembed import (
    SparseTextEmbedding,
    TextEmbedding,
)


DENSE_MODEL = (
    "jinaai/"
    "jina-embeddings-v2-base-code"
)

SPARSE_MODEL = (
    "Qdrant/bm25"
)


class EmbeddingService:

    def __init__(self):

        self.dense_model = (
            TextEmbedding(
                model_name=(
                    DENSE_MODEL
                )
            )
        )

        self.sparse_model = (
            SparseTextEmbedding(
                model_name=(
                    SPARSE_MODEL
                )
            )
        )

    def dense(
        self,
        texts: list[str],
    ):

        return list(
            self.dense_model.embed(
                texts
            )
        )

    def sparse(
        self,
        texts: list[str],
    ):

        return list(
            self.sparse_model.embed(
                texts
            )
        )