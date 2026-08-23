from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from storage.database import Base

class RepositoryModel(Base):
    __tablename__ = "repos"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    root_path: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        unique=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

class FileModel(Base):
    __tablename__="files"
    __table_args__=(
        UniqueConstraint(
            "repo_id",
            "relative_path",
            name="uq_file_repo_path",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    repo_id: Mapped[int] = mapped_column(
        ForeignKey(
            "repos.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True,
    )

    relative_path: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    language: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
    )

    content_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    size_bytes: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # content_hash incremental indexing 增量索引

class SymbolModel(Base):
    __tablename__="symbols"

    __table_args__=(
        UniqueConstraint(
            "file_id",
            "qualified_name",
            "start_line",
            name="uq_symbol_file_name_line",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    repo_id: Mapped[int] = mapped_column(
        ForeignKey(
            "repos.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    file_id: Mapped[int] = mapped_column(
        ForeignKey(
            "files.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        index=True,
    )

    qualified_name: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    symbol_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    language: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
    )

    start_line: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    end_line: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    signature: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )

    code: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    parent_symbol: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    exported: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )