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

        for result in results:

            print(
                f"""
[{result.score:.0f}]
{result.symbol_type}
{result.qualified_name}

{result.path}
{result.start_line}-{result.end_line}

{result.signature}
-------------------------
"""
            )


if __name__ == "__main__":
    main()