// Phone-side encoder: the same 16-byte packing as protocol/frame.py, in JavaScript.
// LAYOUT and the CRC must match Python exactly; tests/test_js_matches_python.py checks this.

const LAYOUT = [
  ["version", 2], ["device", 10], ["seq", 8], ["hops", 4],
  ["priority", 2], ["confidence", 4], ["injury", 4], ["mobility", 2],
  ["people", 3], ["hazard", 3], ["needs", 3], ["time", 11],
  ["lat", 24], ["lon", 25], ["reserved", 7],
];
const DATA_BYTES = 14;

// CRC-16/CCITT-FALSE, same as protocol/crc.py
function crc16(bytes) {
  let crc = 0xffff;
  for (const b of bytes) {
    crc ^= b << 8;
    for (let i = 0; i < 8; i++) {
      crc = crc & 0x8000 ? ((crc << 1) ^ 0x1021) & 0xffff : (crc << 1) & 0xffff;
    }
  }
  return crc;
}

const latToSteps = (lat) => Math.round(((lat + 90) / 180) * (2 ** 24 - 1));
const lonToSteps = (lon) => Math.round(((lon + 180) / 360) * (2 ** 25 - 1));

// msg has lat/lon in degrees; returns a 16-byte Uint8Array.
// BigInt because 112 bits is far more than a normal JS number can hold exactly (53 bits).
function encodeFrame(msg) {
  const fields = { version: 0, reserved: 0, ...msg,
                   lat: latToSteps(msg.lat), lon: lonToSteps(msg.lon) };
  let value = 0n;
  for (const [name, width] of LAYOUT) {
    const number = BigInt(fields[name]);
    if (number < 0n || number >= 1n << BigInt(width)) {
      throw new Error(`${name}=${number} does not fit in ${width} bits`);
    }
    value = (value << BigInt(width)) | number;
  }

  const frame = new Uint8Array(DATA_BYTES + 2);
  for (let i = DATA_BYTES - 1; i >= 0; i--) {   // lowest byte goes last (big-endian)
    frame[i] = Number(value & 0xffn);
    value >>= 8n;
  }
  const crc = crc16(frame.subarray(0, DATA_BYTES));
  frame[DATA_BYTES] = crc >> 8;
  frame[DATA_BYTES + 1] = crc & 0xff;
  return frame;
}

// Same rule as protocol/triage.py; base priorities come from the gateway's codebook.
function triage(injury, mobility, injuryPriorities) {
  let priority = injuryPriorities[injury];
  if (mobility === 2) priority = Math.max(0, priority - 1);
  return { priority, confidence: 15 };
}

if (typeof module !== "undefined") module.exports = { encodeFrame, crc16, triage, LAYOUT };
