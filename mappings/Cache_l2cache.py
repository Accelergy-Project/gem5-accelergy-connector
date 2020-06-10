gem5_class = "Cache"
accelergy_class = "l2cache"
path = "system.chip"

def criteria(params):
    return params["name"] == "l2cache"

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
    ("read_access", "ReadExReq_hits::total", "ReadSharedReq_hits::total"),
    ("read_miss", "ReadExReq_misses::total", "ReadSharedReq_misses::total"),
    # TODO figure out miss counts
]
