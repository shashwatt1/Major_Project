import os
from pathlib import Path
from uuid import uuid4

from cryptography.fernet import Fernet


def _get_fernet() -> Fernet:
    key = os.getenv("VOICE_AI_ENCRYPTION_KEY")
    if not key:
        raise RuntimeError(
            "VOICE_AI_ENCRYPTION_KEY is not set. "
            "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    return Fernet(key)


def encrypt_bytes(data: bytes) -> bytes:
    f = _get_fernet()
    return f.encrypt(data)


def decrypt_bytes(token: bytes) -> bytes:
    f = _get_fernet()
    return f.decrypt(token)


def encrypt_to_file(data: bytes, out_dir: Path, suffix: str) -> tuple[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    file_id = uuid4().hex
    out_path = out_dir / f"{file_id}{suffix}.enc"
    out_path.write_bytes(encrypt_bytes(data))
    return file_id, out_path


def encrypt_text_to_file(text: str, out_dir: Path) -> tuple[str, Path]:
    return encrypt_to_file(text.encode("utf-8"), out_dir, ".txt")


def encrypt_audio_to_file(audio_bytes: bytes, out_dir: Path, ext: str) -> tuple[str, Path]:
    safe_ext = ext if ext.startswith(".") else f".{ext}"
    return encrypt_to_file(audio_bytes, out_dir, safe_ext)
