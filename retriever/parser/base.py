from abc import ABC, abstractmethod

from retriever.parser.models import Symbol
from retriever.scanner import SourceFile

class SymbolParser(ABC):

    @abstractmethod
    def parse(
        self,
        source_file: SourceFile,
    ) -> list[Symbol]:
        pass