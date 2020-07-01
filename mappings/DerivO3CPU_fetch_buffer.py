gem5_class = "DerivO3CPU"
accelergy_class = "fetch_buffer"
path = "system.chip.cpu"
name_append = "fetch_buffer"

criteria = True

constants = []

attributes = [
    ("entries", "fetchBufferSize")
]

actions = [
    ("access", "fetch.Insts")
]
