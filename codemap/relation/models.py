from dataclasses import dataclass


@dataclass
class Relation:
    edge_type: str
    source_symbol: str | None
    target_name: str
    line: int