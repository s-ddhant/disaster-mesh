"""Round-trip tests: decode(encode(x)) == x for many inputs; corrupted frames are rejected."""

import random

import pytest

from gateway.store import Store
from protocol.crc import crc16
from protocol.frame import FRAME_BYTES, FrameError, bump_hops, decode, encode
from protocol.triage import triage

SAMPLE = {
    "device": 517, "seq": 42, "hops": 0, "priority": 0, "confidence": 15,
    "injury": 2, "mobility": 2, "people": 3, "hazard": 1, "needs": 1,
    "time": 785, "lat": 30.4165, "lon": 77.968,
}
METRES_PER_DEGREE = 111_000


def random_message(rng):
    return {
        "device": rng.randrange(1024), "seq": rng.randrange(256), "hops": rng.randrange(16),
        "priority": rng.randrange(3), "confidence": rng.randrange(16),
        "injury": rng.randrange(16), "mobility": rng.randrange(4), "people": rng.randrange(8),
        "hazard": rng.randrange(8), "needs": rng.randrange(8), "time": rng.randrange(1440),
        "lat": rng.uniform(-90, 90), "lon": rng.uniform(-180, 180),
    }


def assert_same(decoded, original):
    for name, value in original.items():
        if name in ("lat", "lon"):
            assert abs(decoded[name] - value) * METRES_PER_DEGREE < 2, name   # within 2 m
        else:
            assert decoded[name] == value, name


def test_crc_standard_check_value():
    assert crc16(b"123456789") == 0x29B1


def test_frame_is_16_bytes():
    assert len(encode(SAMPLE)) == FRAME_BYTES


def test_round_trip_sample():
    assert_same(decode(encode(SAMPLE)), SAMPLE)


def test_round_trip_10000_random_messages():
    rng = random.Random(7)
    for _ in range(10_000):
        msg = random_message(rng)
        assert_same(decode(encode(msg)), msg)


def test_every_single_bit_flip_is_detected():
    frame = encode(SAMPLE)
    for bit in range(FRAME_BYTES * 8):
        damaged = bytearray(frame)
        damaged[bit // 8] ^= 1 << (bit % 8)
        with pytest.raises(FrameError):
            decode(bytes(damaged))


def test_wrong_length_rejected():
    with pytest.raises(FrameError):
        decode(encode(SAMPLE)[:15])


def test_value_too_big_for_its_field_rejected():
    with pytest.raises(ValueError):
        encode({**SAMPLE, "injury": 16})      # 16 needs 5 bits; injury has 4


def test_relay_bumps_hops_and_keeps_frame_valid():
    relayed = bump_hops(encode(SAMPLE))
    decoded = decode(relayed)
    assert decoded["hops"] == 1
    assert_same({k: v for k, v in decoded.items() if k != "hops"},
                {k: v for k, v in SAMPLE.items() if k != "hops"})


def test_triage_rule():
    assert triage(injury=2, mobility=0)[0] == 0    # heavy bleeding -> RED
    assert triage(injury=9, mobility=0)[0] == 1    # broken bone -> YELLOW
    assert triage(injury=9, mobility=2)[0] == 0    # broken bone + cannot move -> RED
    assert triage(injury=14, mobility=2)[0] == 1   # minor + cannot move -> YELLOW


def test_store_drops_duplicates_even_via_another_route():
    store = Store()
    frame = encode(SAMPLE)
    assert store.add(decode(frame), frame, now=0)
    relayed = bump_hops(frame)                      # same message, arrived with 1 hop
    assert not store.add(decode(relayed), relayed, now=5)


def test_store_orders_red_first_then_oldest():
    store = Store()
    for i, priority in enumerate([2, 0, 1, 0]):
        msg = {**SAMPLE, "seq": i, "priority": priority}
        store.add(decode(encode(msg)), encode(msg), now=i)
    assert [(m["priority"], m["seq"]) for m in store.queue()] == [(0, 1), (0, 3), (1, 2), (2, 0)]
