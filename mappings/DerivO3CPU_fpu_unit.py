gem5_class = "DerivO3CPU"
accelergy_class = "fpu_unit"
path = "system.chip.cpu"
name_append = "fpu"

criteria = True

constants = []

attributes = []

actions = [
    ("fp_instruction", "commit.fp_insts")
]
