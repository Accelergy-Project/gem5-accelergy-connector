gem5_class = "Cache"
accelergy_class = "cache"
path = "system.chip"
name_append = ""

def criteria(params):
    return params["name"] in ["l2cache", "l2"]

constants = [
    ("cache_type", "l2cache"),
    ("n_rd_ports", 1),
    ("n_wr_ports", 1),
    ("n_rdwr_ports", 1),
    ("n_banks", 4)
]

attributes = [
    ("size", "size"),
    ("associativity", "assoc"),
    ("data_latency", "response_latency"),
    ("block_size", "tags.block_size"),
    ("mshr_size", "mshrs"),
    ("tag_size", "tags.entry_size"),
    ("write_buffer_size", "write_buffers"),
]

actions = [
    ("read_access", "ReadExReq_accesses::total", "ReadSharedReq_accesses::total"),
    ("read_miss", "ReadExReq_misses::total", "ReadSharedReq_misses::total"),
    ("write_access", "WritebackDirty_accesses::total"),
    ("write_miss", "WritebackDirty_misses::total"),
]
