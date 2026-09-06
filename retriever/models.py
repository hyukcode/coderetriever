from dataclasses import dataclass


@dataclass
class SearchResult:
    symbol_id: int

    name: str
    qualified_name: str
    symbol_type: str

    path: str
    language: str

    start_line: int
    end_line: int

    signature: str
    code: str

    score: float
    match_type: str