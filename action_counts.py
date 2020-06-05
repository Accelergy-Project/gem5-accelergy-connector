class ActionCounts:
    def __init__(self, arch, stats):
        self.arch = arch
        self.stats = stats
        self.action_map = {}

    def addActionCounts(self, accelergy_class, attr):
        print("Collecting action counts for class " + accelergy_class)
        if accelergy_class in self.arch.archMap:
            for arch_path, source_path in self.arch.archMap[accelergy_class].items():
                for arch_name, source_name in attr:
                    self.addField(arch_path, source_path, arch_name, source_name)

    def addField(self, arch_path, source_path, arch_name, source_name):
        field = source_path + "." + source_name
        if field in self.stats:
            counts = int(self.stats[field])
            if arch_path not in self.action_map:
                self.action_map[arch_path] = []
            self.action_map[arch_path].append({"name": arch_name, "counts": counts})
        else:
            print("\tWARNING: unable to locate field %s for %s.%s" % (field, arch_path, arch_name))

    def get(self):
        action_counts = []
        for path, counts in self.action_map.items():
            action_counts.append({"name": path, "action_counts": counts})
        return action_counts


def populateActionCounts(arch, stats):
    print("\n-------- Populate Action Counts --------")
    action_counts = ActionCounts(arch, stats)

    # process memory controllers
    action_counts.addActionCounts("memory_controller", [
        ("read_access", "num_reads::total"),
    ])

    # process caches
    action_counts.addActionCounts("cache", [
        ("read_access", "ReadReq_hits::total"),
        ("read_miss", "ReadReq_misses::total"),
        ("write_access", "WriteReq_hits::total"),
        ("write_miss", "WriteReq_misses::total"),
    ])

    # process TLBs
    action_counts.addActionCounts("tlb", [
        ("read_access", "read_accesses"),
        ("write_access", "write_accesses"),
    ])

    return action_counts
