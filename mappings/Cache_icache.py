gem5_class = "Cache"
accelergy_class = "cache"
path = "system.chip"

def criteria(params):
    return params["name"] == "icache"

constants = [
    ("n_rd_ports", 1),
    ("n_wr_ports", 1),
    ("n_rdwr_ports", 1),
    ("n_banks", 4)
]

attributes = [
    ("cache_type", "name"),
    ("size", "size"),
    ("associativity", "assoc"),
    ("data_latency", "response_latency"),
    ("block_size", "tags.block_size"),
    ("mshr_size", "mshrs"),
    ("tag_size", "tags.entry_size"),
    ("write_buffer_size", "write_buffers"),
]

actions = [
    # NOTE icache is read only
    ("read_access", "ReadReq_hits::total"),
    ("read_miss", "ReadReq_misses::total"),
]
