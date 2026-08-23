from sqlalchemy import create_engine
from sqlalchemy.orm import (
    DeclarativeBase,
    sessionmaker,
)

DATABASE_URL=(
    "postgresql+psycopg://"
    "retriever:retriever"
    "@localhost:5432/"
    "repo_retriever"
)

engine = create_engine(
    DATABASE_URL,
    echo=False,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)

class Base(DeclarativeBase):
    pass