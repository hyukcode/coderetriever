import hashlib
from pathlib import Path 

from sqlalchemy import select
from sqlalchemy.orm import Session

from retriever.parser.registry import (
    ParserRegistry,
)
from retriever.scanner import RepoScanner
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

        source_files = RepoScanner(
            repo_path
        )

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
        