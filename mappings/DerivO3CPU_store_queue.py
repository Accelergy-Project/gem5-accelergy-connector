gem5_class = "DerivO3CPU"
accelergy_class = "load_store_queue"
path = "system.chip.cpu"
name_append = "store_queue"

criteria = True

constants = [
    ("type", "store")
]

attributes = [
    ("entries", "SQEntries")
]

actions = [
    ("load", "iew.iewExecLoadInsts"),
    ("store", "iew.exec_stores")
]
