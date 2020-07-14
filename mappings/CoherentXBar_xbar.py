gem5_class = "CoherentXBar"
accelergy_class = "xbar"
path = "system.chip"
name_append = ""

criteria = True

constants = [
    ("horizontal_nodes", 1),
    ("vertical_nodes", 1),
    ("link_throughput", 1)
]

attributes = [
    ("link_latency", "response_latency"),
    ("flit_bytes", "width")
]

actions = [
    ("access", ["pkt_count::total"])
]
