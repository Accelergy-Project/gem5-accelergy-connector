gem5_class = "DRAMCtrl"
accelergy_class = "dram"
path = "system"
name_append = ""

criteria = False

constants = [
    ("memory_type", "main_memory"),
]

attributes = [
    ("response_latency", "tCL"),
    ("size", "device_size"),
    ("page_size", "device_rowbuffer_size"),
    ("burst_length", "burst_length"),
    ("bus_width", "device_bus_width"),
    ("ranks_per_channel", "ranks_per_channel"),
    ("banks_per_rank", "banks_per_rank"),
    ("port", lambda params: params["port"]["peer"].split(".")[-2]),
]

actions = [
    ("read_access", "num_reads::total"),
]
