gem5_class = "MinorCPU"
accelergy_class = "fpu_unit"
path = "system.chip.cpu"
name_append = "fpu"

criteria = True

constants = []

attributes = []

actions = [
    ("fp_instruction", "fetch2.fp_instructions")
]
