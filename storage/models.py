from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
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
        index=True,
    )

    root_path: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        unique=True,
    )

    created_at: Mapped[datetime] = (
        mapped_column(
            DateTime(
                timezone=True
            ),
            nullable=False,
            server_default=func.now(),
        )
    )

    updated_at: Mapped[datetime] = (
        mapped_column(
            DateTime(
                timezone=True
            ),
            nullable=False,
            server_default=func.now(),
            onupdate=func.now(),
        )
    )


class FileModel(Base):

    __tablename__ = "files"

    __table_args__ = (
        UniqueConstraint(
            "repo_id",
            "relative_path",
            name=(
                "uq_files_repo_path"
            ),
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

    relative_path: Mapped[str] = (
        mapped_column(
            Text,
            nullable=False,
        )
    )

    language: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
    )

    content_hash: Mapped[str] = (
        mapped_column(
            String(64),
            nullable=False,
        )
    )

    size_bytes: Mapped[int] = (
        mapped_column(
            BigInteger,
            nullable=False,
        )
    )

    updated_at: Mapped[datetime] = (
        mapped_column(
            DateTime(
                timezone=True
            ),
            nullable=False,
            server_default=func.now(),
            onupdate=func.now(),
        )
    )


class SymbolModel(Base):

    __tablename__ = "symbols"

    __table_args__ = (
        UniqueConstraint(
            "file_id",
            "qualified_name",
            "start_line",
            name=(
                "uq_symbols_file_qualified_line"
            ),
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

    qualified_name: Mapped[str] = (
        mapped_column(
            Text,
            nullable=False,
            index=True,
        )
    )

    symbol_type: Mapped[str] = (
        mapped_column(
            String(64),
            nullable=False,
            index=True,
        )
    )

    language: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
    )

    start_line: Mapped[int] = (
        mapped_column(
            Integer,
            nullable=False,
        )
    )

    end_line: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    signature: Mapped[str] = (
        mapped_column(
            Text,
            nullable=False,
            default="",
        )
    )

    code: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )

    parent_symbol: Mapped[
        str | None
    ] = mapped_column(
        Text,
        nullable=True,
    )

    exported: Mapped[bool] = (
        mapped_column(
            Boolean,
            nullable=False,
            default=False,
        )
    )


class CodeEdgeModel(Base):

    __tablename__ = "code_edges"

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

    source_file_id: Mapped[int] = (
        mapped_column(
            ForeignKey(
                "files.id",
                ondelete="CASCADE",
            ),
            nullable=False,
            index=True,
        )
    )

    source_symbol_id: Mapped[
        int | None
    ] = mapped_column(
        ForeignKey(
            "symbols.id",
            ondelete="CASCADE",
        ),
        nullable=True,
        index=True,
    )

    target_symbol_id: Mapped[
        int | None
    ] = mapped_column(
        ForeignKey(
            "symbols.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    edge_type: Mapped[str] = (
        mapped_column(
            String(32),
            nullable=False,
            index=True,
        )
    )

    target_name: Mapped[str] = (
        mapped_column(
            Text,
            nullable=False,
        )
    )

    line: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )