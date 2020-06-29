gem5_class = "DerivO3CPU"
accelergy_class = "renaming_unit"
path = "system.chip.cpu"
name_append = "rename_unit"

criteria = True

constants = []

attributes = []

actions = [
    ("read", "rename.RenameLookups"),
    ("write", "rename.RenamedOperands")
]
