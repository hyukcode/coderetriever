import argparse

from retriever.graph.code_map import (
    CodeMapService,
)
from retriever.storage.database import (
    SessionLocal,
)


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "symbol_id",
        type=int,
    )

    parser.add_argument(
        "--depth",
        type=int,
        default=1,
    )

    args = parser.parse_args()

    with SessionLocal() as session:

        service = CodeMapService(
            session
        )

        code_map = (
            service.get_code_map(
                symbol_id=(
                    args.symbol_id
                ),
                depth=args.depth,
            )
        )

        if code_map is None:

            print(
                "Symbol not found."
            )

            return

        nodes = {
            node["symbol_id"]: node
            for node
            in code_map["nodes"]
        }

        root = nodes.get(
            code_map["root"]
        )

        print()
        print("=" * 80)

        if root is not None:

            print(
                f"symbol_id: "
                f"{root['symbol_id']}"
            )

            print(
                f"symbol: "
                f"{root['qualified_name']}"
            )

            print(
                f"type: "
                f"{root['symbol_type']}"
            )

            print(
                f"language: "
                f"{root['language']}"
            )

            print(
                f"path: "
                f"{root['path']}"
            )

            print(
                f"lines: "
                f"{root['start_line']}"
                f"-"
                f"{root['end_line']}"
            )

        print()
        print("RELATIONS")
        print("-" * 80)

        if not code_map["edges"]:

            print(
                "No relations found."
            )

            return

        for edge in (
            code_map["edges"]
        ):

            source_id = (
                edge[
                    "source_symbol_id"
                ]
            )

            target_id = (
                edge[
                    "target_symbol_id"
                ]
            )

            source_node = (
                nodes.get(
                    source_id
                )
                if source_id is not None
                else None
            )

            target_node = (
                nodes.get(
                    target_id
                )
                if target_id is not None
                else None
            )

            if source_node is None:
                source_name = "<file>"
            else:
                source_name = (
                    source_node[
                        "qualified_name"
                    ]
                )

            if target_node is None:
                target_name = (
                    edge[
                        "target_name"
                    ]
                )
            else:
                target_name = (
                    target_node[
                        "qualified_name"
                    ]
                )

            state = (
                "resolved"
                if edge["resolved"]
                else "unresolved"
            )

            print(
                source_name
            )

            print(
                f"  --"
                f"{edge['type']}"
                f"--> "
                f"{target_name}"
            )

            print(
                f"  line="
                f"{edge['line']} "
                f"{state}"
            )

            print()


if __name__ == "__main__":
    main()