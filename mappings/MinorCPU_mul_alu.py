gem5_class = "MinorCPU"
accelergy_class = "func_unit"
path = "system.chip.cpu"
name_append = "mul_alu"

criteria = True

constants = [
    ("type", "mul_alu")
]

attributes = []

actions = [
    ("instruction", "op_class_0::IntMult", "op_class_0::IntDiv"),
    ("idle", "CYCLES")
]
