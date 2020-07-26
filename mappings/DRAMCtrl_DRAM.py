gem5_class = "DRAMCtrl"
accelergy_class = "DRAM"
path = "system"
name_append = ""

criteria = True

constants = [
    ("type", "LPDDR"),
]

attributes = [
    ("width", lambda params: params["device_bus_width"] * 8),
]

actions = [
    ("read", ["num_reads::total"]),
    ("write", ["num_writes::total"]),
    ("idle", ["system.cpu.numCycles"], ["num_reads::total", "num_writes::total"])
]
