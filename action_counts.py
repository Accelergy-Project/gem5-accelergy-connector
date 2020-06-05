class ActionCounts:
    def __init__(self, stats):
        self.stats = stats
        self.action_map = {}

    def add(self, arch_path, source_path, arch_name, source_name):
        field = source_path + "." + source_name
        if field in self.stats:
            counts = int(self.stats[field])
            if arch_path not in self.action_map:
                self.action_map[arch_path] = []
            self.action_map[arch_path].append({"name": arch_name, "counts": counts})
        else:
            print("WARNING: unable to locate field %s for %s.%s" % (field, arch_path, arch_name))

    def get(self):
        action_counts = []
        for path, counts in self.action_map.items():
            action_counts.append({"name": path, "action_counts": counts})
        return action_counts
