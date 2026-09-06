import argparse

from indexer.repo_indexer import (
    RepoIndexer,
)
from storage.database import (
    SessionLocal,
)


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "repo_path",
        help="Repository path",
    )

    args = parser.parse_args()

    with SessionLocal() as session:

        indexer = RepoIndexer(
            session
        )

        indexer.index(
            args.repo_path
        )


if __name__ == "__main__":
    main()