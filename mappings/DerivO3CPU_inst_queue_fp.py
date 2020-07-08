gem5_class = "DerivO3CPU"
accelergy_class = "inst_queue"
path = "system.chip.cpu"
name_append = "inst_queue_fp"

criteria = True

constants = [
    ("type", "fp")
]

attributes = [
    ("entries", "fetchQueueSize"),
    ("issue_width", "issueWidth")
]

actions = [
    ("read", "iq.fp_inst_queue_reads"),
    ("write", "iq.fp_inst_queue_wakeup_accesses"),
    ("wakeup", "iq.fp_inst_queue_writes")
]
