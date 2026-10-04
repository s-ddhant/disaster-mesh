"""Encoder and decoder for the 16-byte frame.

encode(fields) -> 16 bytes, decode(16 bytes) -> fields.
Bit layout: E:/AgentContext/disaster-mesh-wire-spec.md
"""

from protocol.crc import crc16

VERSION = 0

# The agreement between phone and gateway: field order and width in bits.
# phone/frame.js holds an identical copy - change both or neither.
LAYOUT = [
    ("version", 2),
    ("device", 10),
    ("seq", 8),
    ("hops", 4),
    ("priority", 2),
    ("confidence", 4),
    ("injury", 4),
    ("mobility", 2),
    ("people", 3),
    ("hazard", 3),
    ("needs", 3),
    ("time", 11),        # minute of day, UTC
    ("lat", 24),
    ("lon", 25),
    ("reserved", 7),
]
DATA_BYTES = 14          # 112 bits of fields
FRAME_BYTES = 16         # + 2 bytes CRC-16

LAT_BITS, LON_BITS = 24, 25


class FrameError(ValueError):
    """Raised for a frame that is malformed or failed its checksum."""


# --- location: degrees <-> whole-number steps --------------------------------

def lat_to_steps(lat: float) -> int:
    return round((lat + 90) / 180 * (2**LAT_BITS - 1))


def steps_to_lat(steps: int) -> float:
    return steps / (2**LAT_BITS - 1) * 180 - 90


def lon_to_steps(lon: float) -> int:
    return round((lon + 180) / 360 * (2**LON_BITS - 1))


def steps_to_lon(steps: int) -> float:
    return steps / (2**LON_BITS - 1) * 360 - 180


# --- encode / decode ---------------------------------------------------------

def encode(msg: dict) -> bytes:
    """Pack a message (lat/lon in degrees) into a 16-byte frame."""
    fields = dict(msg)
    fields.setdefault("version", VERSION)
    fields.setdefault("reserved", 0)
    fields["lat"] = lat_to_steps(msg["lat"])
    fields["lon"] = lon_to_steps(msg["lon"])

    value = 0
    for name, width in LAYOUT:
        number = fields[name]
        if not 0 <= number < 2**width:
            raise ValueError(f"{name}={number} does not fit in {width} bits")
        value = value << width
        value = value | number

    data = value.to_bytes(DATA_BYTES, "big")
    return data + crc16(data).to_bytes(2, "big")


def decode(frame: bytes) -> dict:
    """Unpack a 16-byte frame. Raises FrameError if it is damaged."""
    if len(frame) != FRAME_BYTES:
        raise FrameError(f"expected {FRAME_BYTES} bytes, got {len(frame)}")
    data, received_crc = frame[:DATA_BYTES], int.from_bytes(frame[DATA_BYTES:], "big")
    if crc16(data) != received_crc:
        raise FrameError("checksum mismatch - frame damaged in transit")

    value = int.from_bytes(data, "big")
    fields = {}
    for name, width in reversed(LAYOUT):      # last field sits in the lowest bits
        fields[name] = value & (2**width - 1)  # keep only the bottom `width` bits
        value = value >> width                 # drop them, exposing the next field

    fields["lat"] = steps_to_lat(fields["lat"])
    fields["lon"] = steps_to_lon(fields["lon"])
    del fields["reserved"]
    return fields


def bump_hops(frame: bytes) -> bytes:
    """What a relay does: hop count +1, then a fresh CRC (the old one no longer matches)."""
    fields = decode(frame)
    fields["hops"] = min(fields["hops"] + 1, 15)
    return encode(fields)
