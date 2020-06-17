gem5_class = "Cache"
accelergy_class = "cache"
path = "system.chip"
name_append = ""

def criteria(params):
    return params["name"] == "l2cache"

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
    # l2cache uses coherency actions ReadEx and ReadShared
    ("read_access", "ReadExReq_accesses::total", "ReadSharedReq_accesses::total"),
    ("read_miss", "ReadExReq_misses::total", "ReadSharedReq_misses::total"),
]
