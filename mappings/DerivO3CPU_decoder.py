gem5_class = "DerivO3CPU"
accelergy_class = "decoder"
path = "system.chip.cpu"
name_append = "decoder"

criteria = True

constants = []

attributes = [
    ("width", "decodeWidth")
]

actions = [
    ("access", ["fetch.Insts"])
]
