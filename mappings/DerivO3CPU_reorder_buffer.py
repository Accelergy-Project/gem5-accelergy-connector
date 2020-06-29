gem5_class = "DerivO3CPU"
accelergy_class = "reorder_buffer"
path = "system.chip.cpu"
name_append = "reorder_buffer"

criteria = True

constants = []

attributes = [
    ("entries", "numROBEntries")
]

actions = [
    ("read", "rob.rob_reads"),
    ("write", "rob.rob_writes")
]
