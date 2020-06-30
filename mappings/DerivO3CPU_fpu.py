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
    ("instruction",
     "commit.op_class_0::FloatAdd",
     "commit.op_class_0::FloatCmp",
     "commit.op_class_0::FloatCvt",
     "commit.op_class_0::FloatMult",
     "commit.op_class_0::FloatMultAcc",
     "commit.op_class_0::FloatDiv",
     "commit.op_class_0::FloatMisc",
     "commit.op_class_0::FloatSqrt"),
    ("idle", "CYCLES")
]
