"""FHOS IPC Protocol v1 — shared constants and helpers."""

from __future__ import annotations

import json
import struct
from typing import Any, Dict, Tuple

MAGIC = 0x46484F53  # "FHOS"
VERSION = 0x01
HEADER_FORMAT = ">IBBHII"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

# Message types
MSG_PING = 0x01
MSG_PONG = 0x02
MSG_DISPATCH = 0x10
MSG_DISPATCH_RESPONSE = 0x11
MSG_MATH_STATUS = 0x20
MSG_ORCHESTRATOR_STATUS = 0x21
MSG_LIST_MODULES = 0x22
MSG_ERROR = 0xFF

DEFAULT_TCP_HOST = "127.0.0.1"
DEFAULT_TCP_PORT = 19753
DEFAULT_UNIX_PATH = "/tmp/fusion_hero_ipc.sock"


def pack_message(msg_type: int, payload: bytes = b"", status_code: int = 0) -> bytes:
    header = struct.pack(
        HEADER_FORMAT,
        MAGIC,
        VERSION,
        msg_type,
        status_code,
        len(payload),
        0,
    )
    return header + payload


def unpack_header(data: bytes) -> Tuple[int, int, int, int, int, int]:
    if len(data) < HEADER_SIZE:
        raise ValueError("incomplete header")
    magic, version, msg_type, status_code, payload_len, reserved = struct.unpack(
        HEADER_FORMAT, data[:HEADER_SIZE]
    )
    if magic != MAGIC:
        raise ValueError(f"invalid magic: 0x{magic:08X}")
    if version != VERSION:
        raise ValueError(f"version mismatch: {version}")
    return magic, version, msg_type, status_code, payload_len, reserved


def json_payload(obj: Any) -> bytes:
    return json.dumps(obj, ensure_ascii=False).encode("utf-8")


def parse_json_payload(data: bytes) -> Any:
    if not data:
        return {}
    return json.loads(data.decode("utf-8"))