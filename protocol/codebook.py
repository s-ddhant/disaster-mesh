"""Codebooks: the code number -> meaning lists (injury, mobility, people, hazard, needs, priority).

The single source of truth. Encoder, decoder and dashboard all read from here.
A list index IS the code that travels in the frame: INJURY[2] == "Heavy bleeding".
"""

RED, YELLOW, GREEN = 0, 1, 2
PRIORITY = ["RED", "YELLOW", "GREEN", "RESERVED"]

# (label, base priority) - frozen 2026-09-30, see wire spec
INJURY = [
    ("Not injured / not stated", GREEN),
    ("Not breathing properly / choking on dust", RED),
    ("Heavy bleeding", RED),
    ("Head injury", RED),
    ("Trapped / crushed under debris", RED),
    ("Buried in snow", RED),
    ("Severe cold / hypothermia", RED),
    ("Chest pain / heart problem", RED),
    ("Serious burns", YELLOW),
    ("Broken bone", YELLOW),
    ("Spine or neck injury", YELLOW),
    ("Unconscious person", RED),
    ("Amputation / limb severed", RED),
    ("Needs medical care (pregnancy, diabetes, asthma...)", YELLOW),
    ("Minor injury or shock", GREEN),
    ("Other / unknown", YELLOW),
]

CANNOT_MOVE = 2
MOBILITY = ["Can walk", "Can move but not walk", "Cannot move", "Unknown"]

PEOPLE = ["Unknown", "1", "2", "3", "4-5", "6-10", "11-20", "More than 20"]

HAZARD = [
    "None", "Fire", "Gas leak", "Flooding",
    "More collapse risk", "More avalanche risk", "Electrical", "Other",
]

NEEDS = [
    "None", "Medical", "Water / food", "Warmth / shelter",
    "Digging equipment", "Evacuation", "Light / communication", "Other",
]
