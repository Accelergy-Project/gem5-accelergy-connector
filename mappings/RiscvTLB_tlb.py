gem5_class = "RiscvTLB"
accelergy_class = "tlb"
path = "system.chip.cpu"
name_append = ""

criteria = True

constants = []

attributes = [
    ("entries", "size"),
]

actions = [
    ("hit", ["hits"]),
    ("miss", ["misses"])
]
