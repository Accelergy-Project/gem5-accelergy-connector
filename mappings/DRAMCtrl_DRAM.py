gem5_class = "DRAMCtrl"
accelergy_class = "DRAM"
path = "system"
name_append = ""

criteria = True

constants = [
    ("type", "LPDDR"),
    ("width", 512)
]

attributes = []

actions = [
    ("read", ["num_reads::total"]),
    ("write", ["num_writes::total"]),
    ("idle", ["system.cpu.numCycles", "system.switch_cpus.numCycles"], ["num_reads::total", "num_writes::total"])
]
