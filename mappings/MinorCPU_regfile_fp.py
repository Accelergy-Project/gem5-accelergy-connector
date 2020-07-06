gem5_class = "MinorCPU"
accelergy_class = "cpu_regfile"
path = "system.chip.cpu"
name_append = "regfile_fp"

criteria = True

constants = [
    ("type", "fp"),
    ("phys_size", 64)
]

attributes = []

# assuming alu actions are 2R1W
actions = [
    ("read",
        "op_class_0::FloatAdd", "op_class_0::FloatAdd",
        "op_class_0::FloatCmp", "op_class_0::FloatCmp",
        "op_class_0::FloatCvt", "op_class_0::FloatCvt",
        "op_class_0::FloatMult", "op_class_0::FloatMult",
        "op_class_0::FloatMultAcc", "op_class_0::FloatMultAcc",
        "op_class_0::FloatDiv", "op_class_0::FloatDiv",
        "op_class_0::FloatMisc",
        "op_class_0::FloatSqrt",
        "op_class_0::FloatMemWrite"),
    ("write",
        "op_class_0::FloatAdd",
        "op_class_0::FloatCmp",
        "op_class_0::FloatCvt",
        "op_class_0::FloatMult",
        "op_class_0::FloatMultAcc",
        "op_class_0::FloatDiv",
        "op_class_0::FloatMisc",
        "op_class_0::FloatSqrt",
        "op_class_0::FloatMemRead")
]
