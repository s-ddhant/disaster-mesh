"""CRC-16 checksum: compute it when sending, check it when receiving (FR6).

Variant: CRC-16/CCITT-FALSE (poly 0x1021, init 0xFFFF, no reflection).
The phone (phone/frame.js) uses the exact same algorithm, so both sides agree.
Standard check value: crc16(b"123456789") == 0x29B1.
"""

POLY = 0x1021
INIT = 0xFFFF


def crc16(data: bytes) -> int:
    crc = INIT
    for byte in data:
        crc ^= byte << 8                      # bring the next byte into the top 8 bits
        for _ in range(8):                    # then process it one bit at a time
            if crc & 0x8000:                  # top bit set -> shift and "divide" by POLY
                crc = ((crc << 1) ^ POLY) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc
