gem5_class = "DerivO3CPU"
accelergy_class = "load_store_queue"
path = "system.chip.cpu"
name_append = "load_queue"

criteria = True

constants = [
    ("type", "load")
]

attributes = [
    ("entries", "LQEntries")
]

actions = [
    ("access", "iew.iewExecLoadInsts")
]
