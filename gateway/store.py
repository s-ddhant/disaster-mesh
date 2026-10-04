"""Message store: duplicate filter on (device, seq) and the priority-ordered queue (RED first, then oldest)."""

import time

DEDUP_WINDOW_S = 30 * 60   # seq wraps at 256, so only remember keys for 30 minutes


class Store:
    def __init__(self):
        self.messages = []
        self._seen = {}       # (device, seq) -> time first received

    def add(self, fields: dict, frame: bytes, now: float | None = None) -> bool:
        """Store a decoded message. Returns False if it is a duplicate (FR9)."""
        now = time.time() if now is None else now
        self._seen = {k: t for k, t in self._seen.items() if now - t < DEDUP_WINDOW_S}

        key = (fields["device"], fields["seq"])   # hops left out: same message via two routes
        if key in self._seen:
            return False
        self._seen[key] = now
        self.messages.append({**fields, "received_at": now, "frame_hex": frame.hex(" ")})
        return True

    def queue(self) -> list[dict]:
        """Most urgent first; within a priority, the one waiting longest first (FR7)."""
        return sorted(self.messages, key=lambda m: (m["priority"], m["received_at"], m["hops"]))
