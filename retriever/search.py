import argparse

from retriever.retriever import (
    CodeRetriever,
)
from storage.database import (
    SessionLocal,
)


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "repo"
    )

    parser.add_argument(
        "query"
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=10,
    )

    args = parser.parse_args()

    with SessionLocal() as session:

        retriever = CodeRetriever(
            session
        )

        results = (
            retriever.search_code(
                repo=args.repo,
                query=args.query,
                top_k=args.top_k,
            )
        )

        if not results:
            print(
                "No results found."
            )

            return

        for index, result in enumerate(
            results,
            start=1,
        ):

            print()
            print(
                "=" * 80
            )

            print(
                f"#{index}"
            )

            print(
                f"score: "
                f"{result.score:.6f}"
            )

            print(
                f"retrieval: "
                f"{result.match_type}"
            )

            print(
                f"type: "
                f"{result.symbol_type}"
            )

            print(
                f"language: "
                f"{result.language}"
            )

            print(
                f"symbol: "
                f"{result.qualified_name}"
            )

            print(
                f"path: "
                f"{result.path}"
            )

            print(
                f"lines: "
                f"{result.start_line}"
                f"-"
                f"{result.end_line}"
            )

            print()

            print(
                result.signature
            )


if __name__ == "__main__":
    main()