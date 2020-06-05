class Arch:
    def __init__(self, connector_config, source_config):
        self.arch = {"name": "system"}  # architecture tree
        self.connector_config = connector_config
        self.source_config = source_config
        self.archMap = {}                              # component map from arch to source
        self.classMap = connector_config["class_map"]  # class map from accelergy to gem5
        self.classInstances = {}                       # instances of each gem5 class in source

        def buildClassInstances(source, path):
            if "type" in source:
                if source["type"] not in self.classInstances:
                    self.classInstances[source["type"]] = []
                self.classInstances[source["type"]].append(path)
            for key, value in source.items():
                if type(value) == dict:
                    buildClassInstances(value, path + "." + key)
        buildClassInstances(source_config["system"], "system")

    def addComponents(self, path, accelergyClass, staticAttr, sourceAttr, dynamicAttr=()):
        gemClass = self.classMap[accelergyClass]
        print("Converting class", gemClass, "->", accelergyClass)
        components = self.classInstances[gemClass] if gemClass in self.classInstances else []
        for component in components:
            name = component.split(".")[-1]
            self.addLocal(path, name, accelergyClass)
            fullName = path + "." + name
            for attr in staticAttr:
                if attr[1] is not None:
                    self.addAttr(fullName, attr[0], attr[1])
            for attr in sourceAttr:
                self.addSourceAttr(fullName, attr[0], component, attr[1])
            if dynamicAttr:
                params = self.getSource(component)
                for attr in dynamicAttr:
                    self.addAttr(fullName, attr[0], attr[1](params))
            # update component map
            if accelergyClass not in self.archMap:
                self.archMap[accelergyClass] = {}
            self.archMap[accelergyClass][fullName] = component
            print("\t%s -> %s" % (component, fullName))
        if not components:
            print("\t NO MATCHES FOUND")

    def addSubtree(self, path, name):
        component = self.getComponent(path)
        if "subtree" not in component:
            component["subtree"] = []
        component["subtree"].append({"name": name})

    def addLocal(self, path, name, accelergyType):
        component = self.getComponent(path)
        if "local" not in component:
            component["local"] = []
        component["local"].append({"name": name, "class": accelergyType})

    def addSystemAttr(self, name):
        value = self.connector_config["system_attributes"][name]
        if value is not None:
            self.addAttr("system", name, value)
        else:
            raise Exception("Unable to find system attribute " + name)

    def addSourceAttr(self, path, name, sourcePath, field):
        value = self.getSourceField(sourcePath, field)
        if value is not None:
            self.addAttr(path, name, value)

    def addAttr(self, path, name, value):
        component = self.getComponent(path)
        if "attributes" not in component:
            component["attributes"] = {}
        component["attributes"][name] = value

    def getComponent(self, path):
        def getSubcomponent(subcomponents, name):
            for subcomponent in subcomponents:
                if subcomponent["name"] == name:
                    return subcomponent
            return None
        names = path.split(".")
        if names[0] == self.arch["name"]:
            component = self.arch
        else:
            raise Exception("Unable to find component " + path)
        for name in names[1:]:
            nextComponent = None
            if "local" in component:
                nextComponent = getSubcomponent(component["local"], name)
            if nextComponent is None and "subtree" in component:
                nextComponent = getSubcomponent(component["subtree"], name)
            if nextComponent is None:
                raise Exception("Unable to find component " + path)
            component = nextComponent
        return component

    def getSource(self, path):
        names = path.split(".")
        source = self.source_config
        for name in names:
            if name in source:
                source = source[name]
            else:
                raise Exception("Unable to find source component" + path)
        return source

    def getSourceField(self, path, field):
        source = self.getSource(path)
        names = field.split(".")
        for name in names[:-1]:
            if name in source:
                source = source[name]
            else:
                print("\tWARNING: cannot locate attribute %s.%s" % (path, field))
                return None
        if names[-1] in source:
            value = source[names[-1]]
            if type(value) == list and len(value) == 1:  # unwrap lists of length 1
                return value[0]
            else:
                return value
        else:
            print("\tWARNING: cannot locate attribute %s.%s" % (path, field))
            return None


def populateArch(connector_config, source_config):
    print("\n-------- Populate Architecture  --------")
    arch = Arch(connector_config, source_config)

    # system attributes
    arch.addSystemAttr("technology")
    arch.addSystemAttr("datawidth")
    arch.addSourceAttr("system", "clockrate", "system.clk_domain", "clock")  # FIXME this is in ps not mHz
    arch.addSourceAttr("system", "block_size", "system", "cache_line_size")
    arch.addSourceAttr("system", "vdd", "system.clk_domain.voltage_domain", "voltage")

    # chip attributes
    arch.addSubtree("system", "chip")
    arch.addSourceAttr("system.chip", "number_hardware_threads", "system.cpu", "numThreads")

    # add memory controllers
    arch.addComponents("system", "memory_controller", [
        ("memory_type", "main_memory"),
    ], [
                           ("response_latency", "tCL"),
                           ("size", "device_size"),
                           ("page_size", "device_rowbuffer_size"),
                           ("burst_length", "burst_length"),
                           ("bus_width", "device_bus_width"),
                           ("ranks_per_channel", "ranks_per_channel"),
                           ("banks_per_rank", "banks_per_rank"),
                       ], [
                           ("port", lambda params: params["port"]["peer"].split(".")[-2])
                       ])

    # add caches
    arch.addComponents("system.chip", "cache", [], [
        ("cache_type", "name"),
        ("replacement_policy", "replacement_policy.type"),
        ("associativity", "assoc"),
        ("block_size", "tags.block_size"),
        ("tag_size", "tags.entry_size"),
        ("write_buffers", "write_buffers"),
        ("size", "size"),
        ("mshrs", "mshrs"),
        ("response_latency", "response_latency"),
    ])

    # add coherent xbars
    arch.addComponents("system.chip", "coherentxbar", [], [
        ("response_latency", "response_latency"),
        ("protocol_response_latency", "snoop_filter.lookup_latency"),
        ("width", "width"),
    ])

    # add TLBs
    arch.addComponents("system.chip", "tlb", [], [
        ("number_entries", "size"),
    ])

    # add exec
    gemCPU = arch.classMap["cpu"]
    if gemCPU in arch.classInstances and len(arch.classInstances[gemCPU]) == 1:
        cpu = arch.classInstances[gemCPU][0]
    else:
        raise Exception("Unable to locate cpu " + gemCPU)
    arch.addComponents("system.chip", "exec", [
        ("instruction_buffer_size", arch.getSourceField(cpu, "executeInputBufferSize")),
        ("issue_width", arch.getSourceField(cpu, "executeIssueLimit")),
        ("commit_width", arch.getSourceField(cpu, "executeCommitLimit")),
        ("store_buffer_size", arch.getSourceField(cpu, "executeLSQStoreBufferSize")),
        ("prediction_width", arch.getSourceField(cpu, "branchPred.numThreads")),
        ("alu_units", 1), # FIXME count functional units
        ("mul_units", 1),
        ("fpu_units", 1),
    ], [])

    return arch
