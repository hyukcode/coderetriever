from sqlalchemy import (
    case,
    func,
    or_,
    select,
)
from sqlalchemy.orm import Session

from storage.models import (
    FileModel,
    RepositoryModel,
    SymbolModel,
)

from .models import (
    SearchResult,
)


class SymbolSearch:

    def __init__(
        self,
        session: Session,
    ):
        self.session = session

    def search(
        self,
        repo: str,
        query: str,
        top_k: int = 20,
    ) -> list[SearchResult]:

        query = query.strip()

        if not query:
            return []

        repo_model = self._find_repo(
            repo
        )

        if repo_model is None:
            return []

        rows = self._search_symbols(
            repo_id=repo_model.id,
            query=query,
            top_k=top_k,
        )

        return [
            self._to_result(row)
            for row in rows
        ]

    def _find_repo(
        self,
        repo: str,
    ):

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

    def _search_symbols(
        self,
        repo_id: int,
        query: str,
        top_k: int,
    ):

        normalized = query.lower()

        contains = f"%{normalized}%"
        prefix = f"{normalized}%"

        score = case(

            (
                func.lower(
                    SymbolModel.name
                ) == normalized,
                100,
            ),

            (
                func.lower(
                    SymbolModel.qualified_name
                ) == normalized,
                95,
            ),

            (
                func.lower(
                    SymbolModel.name
                ).like(prefix),
                80,
            ),

            (
                func.lower(
                    SymbolModel.qualified_name
                ).like(contains),
                70,
            ),

            (
                func.lower(
                    SymbolModel.name
                ).like(contains),
                65,
            ),

            (
                func.lower(
                    FileModel.relative_path
                ).like(contains),
                50,
            ),

            (
                func.lower(
                    SymbolModel.signature
                ).like(contains),
                40,
            ),

            (
                func.lower(
                    SymbolModel.code
                ).like(contains),
                20,
            ),

            else_=0,
        ).label("score")

        stmt = (
            select(
                SymbolModel,
                FileModel.relative_path,
                score,
            )
            .join(
                FileModel,
                FileModel.id
                == SymbolModel.file_id,
            )
            .where(
                SymbolModel.repo_id
                == repo_id
            )
            .where(
                or_(
                    func.lower(
                        SymbolModel.name
                    ).like(contains),

                    func.lower(
                        SymbolModel.qualified_name
                    ).like(contains),

                    func.lower(
                        FileModel.relative_path
                    ).like(contains),

                    func.lower(
                        SymbolModel.signature
                    ).like(contains),

                    func.lower(
                        SymbolModel.code
                    ).like(contains),
                )
            )
            .order_by(
                score.desc()
            )
            .limit(top_k)
        )

        return self.session.execute(
            stmt
        ).all()

    def _to_result(
        self,
        row,
    ) -> SearchResult:

        symbol = row[0]
        path = row[1]
        score = float(row[2])

        return SearchResult(
            symbol_id=symbol.id,

            name=symbol.name,

            qualified_name=(
                symbol.qualified_name
            ),

            symbol_type=(
                symbol.symbol_type
            ),

            path=path,

            language=symbol.language,

            start_line=(
                symbol.start_line
            ),

            end_line=(
                symbol.end_line
            ),

            signature=(
                symbol.signature
            ),

            code=symbol.code,

            score=score,

            match_type=(
                self._match_type(
                    symbol,
                    path,
                )
            ),
        )

    def _match_type(
        self,
        symbol,
        path,
    ) -> str:

        return "symbol"

