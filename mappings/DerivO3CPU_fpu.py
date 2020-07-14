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
    ("access", ["iq.fp_alu_accesses"]),
    ("idle", ["system.cpu.numCycles"], ["iq.fp_alu_accesses"])
]
