gem5_class = "DerivO3CPU"
accelergy_class = "renaming_unit"
path = "system.chip.cpu"
name_append = "rename_unit"

criteria = True

constants = []

attributes = [
    ("decode_width", "decodeWidth"),
    ("commit_width", "commitWidth"),
    ("phys_irf_size", "numPhysIntRegs"),
    ("phys_frf_size", "numPhysFloatRegs")
]

actions = [
    ("read", "rename.RenameLookups"),
    ("write", "rename.RenamedOperands"),
    ("idle", "CYCLES")
]
