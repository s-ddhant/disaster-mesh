"""Midterm triage rule: base priority from the injury code, raised one level if the person cannot move.

Rule-based stand-in for the AI classifier (after the midterm). Confidence is
therefore always the maximum, 15. Mirrors FR5: when in doubt, escalate.
"""

from protocol.codebook import CANNOT_MOVE, INJURY, RED

MAX_CONFIDENCE = 15


def triage(injury: int, mobility: int) -> tuple[int, int]:
    """Return (priority, confidence). Lower priority number = more urgent."""
    priority = INJURY[injury][1]
    if mobility == CANNOT_MOVE:
        priority = max(RED, priority - 1)     # GREEN -> YELLOW -> RED, never past RED
    return priority, MAX_CONFIDENCE
