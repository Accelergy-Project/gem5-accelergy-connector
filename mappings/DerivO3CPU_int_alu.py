gem5_class = "DerivO3CPU"
accelergy_class = "func_unit"
path = "system.chip.cpu"
name_append = "int_alu"

criteria = True

constants = [
    ("type", "int_alu")
]

attributes = []

actions = [
    ("instruction", "commit.op_class_0::IntAlu"),
    ("idle", "CYCLES")
]
