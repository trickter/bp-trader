from __future__ import annotations

import base64
from typing import Any

from .exceptions import BackpackSigningError
from .serialize import batch_signature_payload, signature_payload


def _decode_private_key_bytes(private_key: str | bytes) -> bytes:
    if isinstance(private_key, bytes):
        return private_key

    key = private_key.strip()
    if key.startswith("-----BEGIN"):
        return key.encode("utf-8")

    for decoder in (_decode_base64, _decode_hex):
        try:
            return decoder(key)
        except BackpackSigningError:
            continue

    raise BackpackSigningError("Unsupported Backpack private key format.")


def _decode_base64(value: str) -> bytes:
    try:
        return base64.b64decode(value, validate=True)
    except Exception as exc:  # pragma: no cover - defensive parser
        raise BackpackSigningError("Invalid base64 private key.") from exc


def _decode_hex(value: str) -> bytes:
    try:
        return bytes.fromhex(value)
    except ValueError as exc:
        raise BackpackSigningError("Invalid hex private key.") from exc


def _load_private_key(private_key: str | bytes) -> Any:
    raw = _decode_private_key_bytes(private_key)

    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    except ImportError as exc:  # pragma: no cover - dependency owned by parent integration
        raise BackpackSigningError(
            "cryptography is required for Backpack ED25519 signing."
        ) from exc

    if raw.startswith(b"-----BEGIN"):
        try:
            loaded = serialization.load_pem_private_key(raw, password=None)
        except Exception as exc:  # pragma: no cover - bad PEM
            raise BackpackSigningError("Failed to parse PEM Ed25519 private key.") from exc

        if not isinstance(loaded, Ed25519PrivateKey):
            raise BackpackSigningError("Provided PEM key is not an Ed25519 private key.")

        return loaded

    if len(raw) == 32:
        return Ed25519PrivateKey.from_private_bytes(raw)

    if len(raw) == 64:
        return Ed25519PrivateKey.from_private_bytes(raw[:32])

    raise BackpackSigningError(
        "Backpack private key must be a 32-byte seed, a 64-byte expanded key, or a PEM Ed25519 key."
    )


def sign_instruction(
    *,
    private_key: str | bytes,
    instruction: str,
    params: dict[str, object | None],
    timestamp_ms: int,
    window_ms: int,
) -> str:
    payload = signature_payload(
        instruction=instruction,
        params=params,
        timestamp_ms=timestamp_ms,
        window_ms=window_ms,
    )
    signer = _load_private_key(private_key)
    signature = signer.sign(payload.encode("utf-8"))
    return base64.b64encode(signature).decode("ascii")


def sign_instruction_batch(
    *,
    private_key: str | bytes,
    instruction: str,
    entries: list[dict[str, object | None]],
    timestamp_ms: int,
    window_ms: int,
) -> str:
    payload = batch_signature_payload(
        instruction=instruction,
        entries=entries,
        timestamp_ms=timestamp_ms,
        window_ms=window_ms,
    )
    signer = _load_private_key(private_key)
    signature = signer.sign(payload.encode("utf-8"))
    return base64.b64encode(signature).decode("ascii")
