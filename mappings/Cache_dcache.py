gem5_class = "Cache"
accelergy_class = "dcache"
path = "system.chip"

def criteria(params):
    return params["name"] == "dcache"

constants = []

attributes = [
    ("cache_type", "name"),
    ("replacement_policy", "replacement_policy.type"),
    ("associativity", "assoc"),
    ("block_size", "tags.block_size"),
    ("tag_size", "tags.entry_size"),
    ("write_buffers", "write_buffers"),
    ("size", "size"),
    ("mshrs", "mshrs"),
    ("response_latency", "response_latency"),
]

actions = [
    ("read_access", "ReadReq_hits::total"),
    ("read_miss", "ReadReq_misses::total"),
    ("write_access", "WriteReq_hits::total"),
    ("write_miss", "WriteReq_misses::total"),
]
