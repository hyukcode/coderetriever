from dataclasses import dataclass
from pathlib import pathlib

SUPPORTED_EXTENSION = {
    ".py" : "python",
    ".java": "java",
    ".go": "go",
    ".js": "javascript",
    ".ts": "typescript",
}

IGNORED_DIRS = {
    ".git",
    ".idea"
}