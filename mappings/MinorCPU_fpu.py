gem5_class = "MinorCPU"
accelergy_class = "func_unit"
path = "system.chip.cpu"
name_append = "fpu"

criteria = True

constants = [
    ("type", "fpu")
]

attributes = []

actions = [
    ("access",
     ["op_class_0::FloatAdd",
     "op_class_0::FloatCmp",
     "op_class_0::FloatCvt",
     "op_class_0::FloatMult",
     "op_class_0::FloatMultAcc",
     "op_class_0::FloatDiv",
     "op_class_0::FloatMisc",
     "op_class_0::FloatSqrt"]),
    ("idle", ["system.cpu.numCycles", "system.switch_cpus.numCycles"],
     ["op_class_0::FloatAdd",
      "op_class_0::FloatCmp",
      "op_class_0::FloatCvt",
      "op_class_0::FloatMult",
      "op_class_0::FloatMultAcc",
      "op_class_0::FloatDiv",
      "op_class_0::FloatMisc",
      "op_class_0::FloatSqrt"])
]
