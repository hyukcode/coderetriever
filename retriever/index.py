import argparse

from indexer.repo_indexer import RepoIndexer
from storage.database import SessionLocal


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "repo_path",
        help="Repository path",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Force rebuild repository index",
    )

    args = parser.parse_args()

    with SessionLocal() as session:
        indexer = RepoIndexer(
            session
        )

        indexer.index(
            repo_path=args.repo_path,
            force=args.force,
        )


if __name__ == "__main__":
    main()