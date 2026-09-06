import hashlib
from pathlib import Path

from sqlalchemy import (
    select,
    delete,
)
from sqlalchemy.orm import Session

from retriever.parser.registry import (
    ParserRegistry,
)
from retriever.scanner import (
    RepoScanner,
)
from storage.models import (
    RepositoryModel,
    FileModel,
    SymbolModel
)

class RepoIndexer:
    def __init__(
        self,
        session: Session,
    ):
        self.session = session
        self.parser_registry = (
            ParserRegistry()
        )

    def index(
        self,
        repo_path: str
    ):
        repo_path = str(
            Path(repo_path).resolve()
        )

        repo = self._get_or_create_repo(
            repo_path
        )

        scanner = RepoScanner(
            repo_path
        )

        source_files = scanner.scan()

        print(
            f"found {len(source_files)} files"
        )

        for source_file in source_files:
            self._index_file(
                repo,
                source_file,
            )

        self.session.commit()

    def _get_or_create_repo(
        self,
        repo_path: str,
    ) -> RepositoryModel:
        stmt = select(
            RepositoryModel
        ).where(
            RepositoryModel.root_path == repo_path
        )

        repo = self.session.scalar(
            stmt
        )

        if repo is not None:
            return repo

        repo = RepositoryModel(
            name=Path(repo_path).name,
            root_path=repo_path,
        )

        self.session.add(repo)

        self.session.flush()

        return repo

    def _file_hash(
        self,
        path: Path,
    ) -> str:
        sha256 = hashlib.sha256()
        with path.open("rb") as f:
            while chunk := f.read(
                1024*1024
            ):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _index_file(
        self,
        repo,
        source_file,
    ):

        content_hash = self._file_hash(
            source_file.path
        )

        stmt = select(
            FileModel
        ).where(
            FileModel.repo_id == repo.id,
            FileModel.relative_path
            == source_file.relative_path,
        )

        file_model = self.session.scalar(
            stmt
        )

        if (
            file_model is not None
            and file_model.content_hash
            == content_hash
            and self.session.scalar(
                select(SymbolModel.id)
                .where(SymbolModel.file_id == file_model.id)
                .limit(1)
            ) is not None
        ):
            print(
                "skip:",
                source_file.relative_path,
            )

            return

        parser = (
            self.parser_registry.get(
                source_file.language
            )
        )

        try:

            symbols = parser.parse(
                source_file
            )

        except Exception as exc:

            print(
                "parse failed:",
                source_file.relative_path,
                exc,
            )

            return

        if file_model is None:

            file_model = FileModel(
                repo_id=repo.id,
                relative_path=(
                    source_file.relative_path
                ),
                language=(
                    source_file.language
                ),
                content_hash=content_hash,
                size_bytes=(
                    source_file.path.stat().st_size
                ),
            )

            self.session.add(
                file_model
            )

            self.session.flush()

        else:

            file_model.language = (
                source_file.language
            )

            file_model.content_hash = (
                content_hash
            )

            file_model.size_bytes = (
                source_file.path.stat().st_size
            )

            self._delete_file_symbols(
                file_model.id
            )

        for symbol in symbols:

            symbol_model = SymbolModel(
                repo_id=repo.id,
                file_id=file_model.id,

                name=symbol.name,

                qualified_name=(
                    symbol.qualified_name
                ),

                symbol_type=(
                    symbol.symbol_type
                ),

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

                code=symbol.code,

                parent_symbol=getattr(
                    symbol,
                    "parent_symbol",
                    None,
                ),

                exported=getattr(
                    symbol,
                    "exported",
                    False,
                ),
            )

            self.session.add(
                symbol_model
            )

        print(
            "indexed:",
            source_file.relative_path,
            f"symbols={len(symbols)}",
        )

    def _delete_file_symbols(
        self,
        file_id: int,
    ):

        stmt = delete(
            SymbolModel
        ).where(
            SymbolModel.file_id
            == file_id
        )

        self.session.execute(
            stmt
        )
