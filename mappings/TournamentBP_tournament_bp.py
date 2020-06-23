gem5_class = "TournamentBP"
accelergy_class = "tournament_bp"
path = "system.chip.cpu"
name_append = ""

criteria = True

constants = []

attributes = [
    ("local_pred_entries", "localPredictorSize"),
    ("local_pred_bits", "localCtrBits"),
    ("global_pred_entries", "globalPredictorSize"),
    ("global_pred_bits", "globalCtrBits"),
    ("choice_pred_entries", "choicePredictorSize"),
    ("choice_pred_bits", "choiceCtrBits")
]

actions = [
    ("access", "condPredicted"),
    ("miss", "condIncorrect")
]
