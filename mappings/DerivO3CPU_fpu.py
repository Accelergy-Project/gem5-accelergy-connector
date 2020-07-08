gem5_class = "DerivO3CPU"
accelergy_class = "func_unit"
path = "system.chip.cpu"
name_append = "fpu"

criteria = True

constants = [
    ("type", "fpu")
]

attributes = []

actions = [
    ("instruction", "iq.fp_alu_accesses"),
    ("idle", "CYCLES")
]
