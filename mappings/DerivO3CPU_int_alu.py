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
    ("access", ["iq.int_alu_accesses"]),
    ("idle", ["system.cpu.numCycles", "system.switch_cpus.numCycles"], ["iq.int_alu_accesses"])
]
