import hashlib
import uuid
from dataclasses import dataclass
from pathlib import Path

from app.core.config import settings


@dataclass(frozen=True)
class StoredFile:
    stored_name: str
    relative_path: str
    absolute_path: Path
    checksum_sha256: str


def storage_root() -> Path:
    root = Path(settings.upload_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def store_file(content: bytes, brs_id: uuid.UUID, document_type: str, version: int, extension: str) -> StoredFile:
    safe_extension = extension.lower()
    stored_name = f"v{version}_{uuid.uuid4().hex}{safe_extension}"
    relative_path = Path(str(brs_id)) / document_type / stored_name
    absolute_path = storage_root() / relative_path
    absolute_path.parent.mkdir(parents=True, exist_ok=True)
    absolute_path.write_bytes(content)
    return StoredFile(
        stored_name=stored_name,
        relative_path=relative_path.as_posix(),
        absolute_path=absolute_path,
        checksum_sha256=hashlib.sha256(content).hexdigest(),
    )


def resolve_stored_path(relative_path: str) -> Path:
    root = storage_root()
    path = (root / relative_path).resolve()
    if not path.is_relative_to(root):
        raise ValueError("Lokasi file tidak valid.")
    return path
