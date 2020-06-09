import os
import re
import sys
import yaml
import json
import argparse


def main():
    # python3 connector.py -m example/m5out -i example/input -o example/output -c example/config.yaml
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", help="the gem5 m5out directory path", required=True)
    parser.add_argument("-i", help="the directory path to put the accelergy input", required=True)
    parser.add_argument("-o", help="the directory path to put the accelergy output", required=True)
    parser.add_argument("-c", help="the config file for this converter", required=True)
    parser.add_argument("-d", help="when present accelergy will not be called", action="store_true")
    args = parser.parse_args()
    paths = {
        "m5out": args.m,
        "input": args.i,
        "output": args.o,
        "config": args.c,
    }

    # read connector configuration file
    with open(paths["config"]) as file:
        connector_config = yaml.load(file, Loader=yaml.FullLoader)
    # read gem5 source architecture configuration file
    with open(paths["m5out"] + "/config.json") as f:
        source_config = json.load(f)

    # populate and write architecture
    arch = populateArch(connector_config, source_config)
    arch_yaml = {
        "architecture": {
            "version": 0.3,
            "subtree": [arch.arch]
        }
    }
    if not os.path.exists(paths["input"]):
        os.makedirs(paths["input"])
    with open(paths["input"] + "/architecture.yaml", "w") as file:
        yaml.dump(arch_yaml, file, sort_keys=False)

    # parse stats file
    stats = {}
    with open(paths["m5out"] + "/stats.txt", "r") as file:
        pattern = re.compile(r"(\S+)\s+(\S+).*#")
        for line in file.readlines():
            match = pattern.match(line)
            if match:
                stats[match.group(1)] = match.group(2)

    # populate and write action counts
    action_counts = populateActionCounts(arch, stats)
    action_counts_yaml = {"action_counts": {
        "version": 0.3,
        "local": action_counts.get(),
    }}
    with open(paths["input"] + "/action_counts.yaml", "w") as file:
        yaml.dump(action_counts_yaml, file, sort_keys=False)

    # invoke accelergy
    accelergy_command = "accelergy -o " + paths["output"] + " " + paths["input"] + "/*.yaml " + "components/*.yaml -v 1"
    print("\n-------- Hand-off to Accelergy  --------")
    print(accelergy_command)
    print()
    if not args.d:
        os.system(accelergy_command)


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


if __name__ == "__main__":
    if sys.version_info < (3, 0):
        print("Python 2.x is not supported for connector.py")
        sys.exit(1)
    main()
