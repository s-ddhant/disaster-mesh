"""Reconstruction (FR11): turn decoded fields into a readable brief for rescuers.

A fixed template, not generated text: it can only state what is in the frame,
so it can never invent a detail the victim did not send (NFR6).
"""

from protocol.codebook import HAZARD, INJURY, MOBILITY, NEEDS, PEOPLE, PRIORITY


def describe(f: dict) -> str:
    parts = [
        f"{PRIORITY[f['priority']]}: {INJURY[f['injury']][0]}",
        f"people: {PEOPLE[f['people']]}",
        f"mobility: {MOBILITY[f['mobility']].lower()}",
    ]
    if f["hazard"]:
        parts.append(f"hazard: {HAZARD[f['hazard']].lower()}")
    if f["needs"]:
        parts.append(f"needs: {NEEDS[f['needs']].lower()}")
    return " | ".join(parts)
