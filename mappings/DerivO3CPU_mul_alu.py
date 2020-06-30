gem5_class = "DerivO3CPU"
accelergy_class = "func_unit"
path = "system.chip.cpu"
name_append = "mul_alu"

criteria = True

constants = [
    ("type", "mul_alu")
]

attributes = []

actions = [
    ("instruction", "commit.op_class_0::IntMult", "commit.op_class_0::IntDiv"),
    ("idle", "CYCLES")
]
