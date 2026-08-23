from dataclasses import dataclass
from pathlib import Path 

SUPPORTED_EXTENSION = {
    ".py": "python",
    ".java": "java",
    ".js": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".jsx": "jsx",
}

IGNORED_DIRS = {
    ".git",
    ".idea",
    ".vscode",
    "__pycache__",
    "node_modules",
    "target",
    "build",
    "dist",
    ".venv",
    "venv",
}

@dataclass
class SourceFile:
    path: Path
    relative_path: str 
    language: str

class RepoScanner:
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path).resolve()
    
    def scan(self) -> list[SourceFile]:
        files = []
        for path in self.repo_path.rglob("*"):
            if not path.is_file():
                continue
            if self._should_ignore(path):
                continue
            language = SUPPORTED_EXTENSION.get(path.suffix)
            if language is None:
                continue
            files.append(
                SourceFile(
                    path=path,
                    relative_path=str(
                        path.relative_to(self.repo_path)
                    ),
                    language=language,
                )
            )
        return files

    def _should_ignore(self, path: Path) -> bool:
        return any(
            part in IGNORED_DIRS for part in path.parts
        )