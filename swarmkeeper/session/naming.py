"""Agent name generation with animal suffixes."""

from datetime import datetime

ANIMALS = [
    "bee",
    "ant",
    "wasp",
    "beetle",
    "moth",
    "cricket",
    "spider",
    "ladybug",
    "firefly",
    "dragonfly",
    "mantis",
    "caterpillar",
    "butterfly",
    "hornet",
    "termite",
    "locust",
    "cicada",
    "aphid",
    "roach",
    "flea",
    "gnat",
    "mite",
]


def generate_agent_name(existing_names: list[str]) -> str:
    """Generate unique agent name in format agent-XX-animal.

    Args:
        existing_names: List of already taken session names

    Returns:
        Unique agent name like "agent-01-spider"
    """
    # Extract numbers from existing agent names
    used_numbers = set()
    for name in existing_names:
        if name.startswith("agent-"):
            try:
                num_part = name.split("-")[1]
                if num_part.isdigit():
                    used_numbers.add(int(num_part))
            except (IndexError, ValueError):
                continue

    # Find next available number starting from 1
    counter = 1
    while counter in used_numbers:
        counter += 1

    # Select animal based on counter (cycles through animals)
    animal_index = (counter - 1) % len(ANIMALS)
    animal = ANIMALS[animal_index]

    return f"agent-{counter:02d}-{animal}"
