gem5_class = "TournamentBP"
accelergy_class = "btb"
path = "system.chip.cpu"
name_append = "btb"

criteria = True

constants = [
    ("block_width", 4),
    ("associativity", 2),
    ("banks", 2)
]

attributes = [
    ("entries", "BTBEntries")
]

actions = [
    ("read", "BTBLookups"),
    ("write", "BTBLookups")
]
