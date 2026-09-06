class SymbolDocumentBuilder:

    def build(
        self,
        symbol,
        path: str,
    ) -> str:

        return "\n".join(
            [
                (
                    f"language: "
                    f"{symbol.language}"
                ),

                (
                    f"type: "
                    f"{symbol.symbol_type}"
                ),

                (
                    f"symbol: "
                    f"{symbol.qualified_name}"
                ),

                (
                    f"file: "
                    f"{path}"
                ),

                "",
                "signature:",
                symbol.signature,

                "",
                "code:",
                symbol.code,
            ]
        )