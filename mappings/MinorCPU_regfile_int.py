gem5_class = "MinorCPU"
accelergy_class = "cpu_regfile"
path = "system.chip.cpu"
name_append = "regfile_int"

criteria = True

constants = [
    ("type", "int"),
    ("phys_size", 64)
]

attributes = [
    ("issue_width", "executeIssueLimit")
]

# assuming alu actions are 2R1W
actions = [
    ("read",
     "op_class_0::IntAlu", "op_class_0::IntAlu",
     "op_class_0::IntMult", "op_class_0::IntMult",
     "op_class_0::IntDiv", "op_class_0::IntDiv",
     "op_class_0::MemWrite"),
    ("write",
     "op_class_0::IntAlu",
     "op_class_0::IntMult",
     "op_class_0::IntDiv",
     "op_class_0::MemRead")
]
