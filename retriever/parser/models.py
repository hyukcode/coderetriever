from dataclasses import dataclass

@dataclass
class Symbol:
    name: str
    qualified_name: str
    symbol_type: str
    path: str
    language: str
    start_line: str
    end_line: str
    signature: str
    code: str

