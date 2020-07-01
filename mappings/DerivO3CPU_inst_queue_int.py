gem5_class = "DerivO3CPU"
accelergy_class = "inst_queue"
path = "system.chip.cpu"
name_append = "inst_queue_int"

criteria = True

constants = [
    ("type", "int")
]

attributes = [
    ("entries", "numIQEntries")
]

actions = [
    ("read", "iq.int_inst_queue_reads"),
    ("write", "iq.int_inst_queue_wakeup_accesses"),
    ("wakeup", "iq.int_inst_queue_writes")
]
