from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import os


@dataclass(frozen=True)
class StoredArtifact:
    object_path: str
    size_bytes: int
    checksum_sha256: str


class LocalArtifactStorage:
    def __init__(self, root: str | Path = "generated_artifacts") -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _safe_path(self, object_path: str) -> Path:
        destination = (self.root / object_path).resolve()
        if self.root not in destination.parents:
            raise ValueError("Unsafe artifact path.")
        return destination

    def write(self, object_path: str, content: bytes) -> StoredArtifact:
        destination = self._safe_path(object_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        temporary.write_bytes(content)
        os.replace(temporary, destination)
        return StoredArtifact(object_path, len(content), sha256(content).hexdigest())

    def path(self, object_path: str) -> Path:
        path = self._safe_path(object_path)
        if not path.is_file():
            raise FileNotFoundError(object_path)
        return path

    def delete(self, object_path: str) -> bool:
        try:
            self.path(object_path).unlink()
            return True
        except FileNotFoundError:
            return False
