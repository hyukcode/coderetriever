from sqlalchemy.orm import Session

from retriever.symbol_search import (
    SymbolSearch,
)


class CodeRetriever:

    def __init__(
        self,
        session: Session,
    ):

        self.symbol_search = (
            SymbolSearch(session)
        )

    def search_code(
        self,
        repo: str,
        query: str,
        top_k: int = 10,
    ):

        return self.symbol_search.search(
            repo=repo,
            query=query,
            top_k=top_k,
        )