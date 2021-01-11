gem5_class = "MinorCPU"
accelergy_class = "func_unit"
path = "system.chip.cpu"
name_append = "int_alu"

criteria = True

constants = [
    ("type", "int_alu")
]

attributes = []

actions = [
    ("access", ["op_class_0::IntAlu"]),
    ("idle", ["system.cpu.numCycles", "system.switch_cpus.numCycles"], ["op_class_0::IntAlu"])
]
