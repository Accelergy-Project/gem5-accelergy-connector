gem5_class = "Cache"
accelergy_class = "cache"
path = "system.chip"
name_append = ""

def criteria(params):
    return params["name"] == "icache"

constants = [
    ("cache_type", "icache"),
    ("n_rd_ports", 1),
    ("n_wr_ports", 1),
    ("n_rdwr_ports", 1),
    ("n_banks", 1),
    ("block_size", 32)
]

attributes = [
    ("size", "size"),
    ("associativity", "assoc"),
    ("data_latency", "response_latency"),
    ("mshr_size", "mshrs"),
    ("tag_size", "tags.entry_size"),
    ("write_buffer_size", "write_buffers"),
]

actions = [
    # NOTE icache is read only
    ("read_hit", ["ReadReq_hits::total"]),
    ("read_miss", ["ReadReq_misses::total"]),
]
