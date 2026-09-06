import hashlib
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from retriever.embedding.document_builder import SymbolDocumentBuilder
from retriever.embedding.service import EmbeddingService
from retriever.parser.registry import ParserRegistry
from retriever.scanner import RepoScanner, SourceFile
from storage.models import (
    FileModel,
    RepositoryModel,
    SymbolModel,
)
from retriever.vector.qdrant_store import QdrantStore


class RepoIndexer:

    def __init__(
        self,
        session: Session,
    ):
        self.session = session
        self.parser_registry = ParserRegistry()
        self.embedding_service = EmbeddingService()
        self.document_builder = SymbolDocumentBuilder()
        self.qdrant_store = QdrantStore()
        self.qdrant_store.init_collection()

    def index(
        self,
        repo_path: str,
    ) -> None:

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
            f"[index] repo={repo.name}"
        )

        print(
            f"[index] path={repo.root_path}"
        )

        print(
            f"[index] found "
            f"{len(source_files)} source files"
        )

        indexed_count = 0
        skipped_count = 0
        failed_count = 0

        for source_file in source_files:
            try:
                changed = self._index_file(
                    repo=repo,
                    source_file=source_file,
                )

                if changed:
                    indexed_count += 1
                else:
                    skipped_count += 1

            except Exception as exc:
                failed_count += 1

                self.session.rollback()

                print(
                    "[index] failed:",
                    source_file.relative_path,
                    repr(exc),
                )

                repo = self._find_repo_by_path(
                    repo_path
                )

                if repo is None:
                    raise RuntimeError(
                        "Repository disappeared "
                        "after transaction rollback"
                    ) from exc

        self.session.commit()

        print()
        print("[index] complete")

        print(
            f"[index] indexed={indexed_count}"
        )

        print(
            f"[index] skipped={skipped_count}"
        )

        print(
            f"[index] failed={failed_count}"
        )

    def _index_file(
        self,
        repo: RepositoryModel,
        source_file: SourceFile,
    ) -> bool:

        content_hash = self._file_hash(
            source_file.path
        )

        file_model = self._find_file(
            repo_id=repo.id,
            relative_path=(
                source_file.relative_path
            ),
        )

        if (
            file_model is not None
            and file_model.content_hash
            == content_hash
        ):
            print(
                "[skip]",
                source_file.relative_path,
            )

            return False

        parser = self.parser_registry.get(
            source_file.language
        )

        symbols = parser.parse(
            source_file
        )

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
                    source_file.path
                    .stat()
                    .st_size
                ),
            )

            self.session.add(
                file_model
            )

            self.session.flush()

        else:
            self._delete_file_symbols(
                file_model.id
            )

            file_model.language = (
                source_file.language
            )

            file_model.content_hash = (
                content_hash
            )

            file_model.size_bytes = (
                source_file.path
                .stat()
                .st_size
            )

        symbol_models: list[
            tuple[SymbolModel, object]
        ] = []

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
                    or ""
                ),
                code=(
                    symbol.code
                    or ""
                ),
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

            symbol_models.append(
                (
                    symbol_model,
                    symbol,
                )
            )

        self.session.flush()

        if not symbol_models:
            print(
                "[indexed]",
                source_file.relative_path,
                "symbols=0",
            )

            return True

        documents = [
            self.document_builder.build(
                symbol=symbol,
                path=(
                    source_file.relative_path
                ),
            )
            for _, symbol
            in symbol_models
        ]

        dense_vectors = (
            self.embedding_service.dense(
                documents
            )
        )

        sparse_vectors = (
            self.embedding_service.sparse(
                documents
            )
        )

        if (
            len(dense_vectors)
            != len(symbol_models)
        ):
            raise RuntimeError(
                "Dense embedding count "
                "does not match symbol count"
            )

        if (
            len(sparse_vectors)
            != len(symbol_models)
        ):
            raise RuntimeError(
                "Sparse embedding count "
                "does not match symbol count"
            )

        for (
            (symbol_model, symbol),
            dense_vector,
            sparse_vector,
        ) in zip(
            symbol_models,
            dense_vectors,
            sparse_vectors,
        ):
            self.qdrant_store.upsert_symbol(
                symbol_id=(
                    symbol_model.id
                ),
                repo_id=repo.id,
                path=(
                    source_file.relative_path
                ),
                language=(
                    symbol.language
                ),
                symbol_type=(
                    symbol.symbol_type
                ),
                qualified_name=(
                    symbol.qualified_name
                ),
                dense_vector=(
                    dense_vector
                ),
                sparse_vector=(
                    sparse_vector
                ),
            )

        print(
            "[indexed]",
            source_file.relative_path,
            f"symbols={len(symbol_models)}",
        )

        return True

    def _get_or_create_repo(
        self,
        repo_path: str,
    ) -> RepositoryModel:

        repo = self._find_repo_by_path(
            repo_path
        )

        if repo is not None:
            return repo

        repo = RepositoryModel(
            name=Path(repo_path).name,
            root_path=repo_path,
        )

        self.session.add(
            repo
        )

        self.session.flush()

        return repo

    def _find_repo_by_path(
        self,
        repo_path: str,
    ) -> RepositoryModel | None:

        stmt = (
            select(
                RepositoryModel
            )
            .where(
                RepositoryModel.root_path
                == repo_path
            )
            .limit(1)
        )

        return self.session.scalar(
            stmt
        )

    def _find_file(
        self,
        repo_id: int,
        relative_path: str,
    ) -> FileModel | None:

        stmt = (
            select(
                FileModel
            )
            .where(
                FileModel.repo_id
                == repo_id
            )
            .where(
                FileModel.relative_path
                == relative_path
            )
            .limit(1)
        )

        return self.session.scalar(
            stmt
        )

    def _delete_file_symbols(
        self,
        file_id: int,
    ) -> None:

        stmt = (
            select(
                SymbolModel.id
            )
            .where(
                SymbolModel.file_id
                == file_id
            )
        )

        symbol_ids = list(
            self.session.scalars(
                stmt
            )
        )

        if symbol_ids:
            self.qdrant_store.delete(
                symbol_ids
            )

        delete_stmt = (
            delete(
                SymbolModel
            )
            .where(
                SymbolModel.file_id
                == file_id
            )
        )

        self.session.execute(
            delete_stmt
        )

    def _file_hash(
        self,
        path: Path,
    ) -> str:

        sha256 = hashlib.sha256()

        with path.open("rb") as file:
            while True:
                chunk = file.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                sha256.update(
                    chunk
                )

        return sha256.hexdigest()