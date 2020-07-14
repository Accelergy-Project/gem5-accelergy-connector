import os
import re
import sys
import yaml
import json
import argparse


def main():
    # python3 connector.py -m example/m5out -i example/input -o example/output -c example/attributes.yaml
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", help="the gem5 m5out directory path", required=True)
    parser.add_argument("-i", help="the directory to put the accelergy input", required=True)
    parser.add_argument("-o", help="the directory to put the accelergy output", required=True)
    parser.add_argument("-a", help="the attributes file for this converter", required=True)
    parser.add_argument("-d", help="when present accelergy will not be called", action="store_true")
    parser.add_argument("-v", help="when present output will be verbose", action="store_true")
    args = parser.parse_args()
    paths = {
        "m5out": args.m,
        "input": args.i,
        "output": args.o,
        "attributes": args.a,
        "mappings": "mappings"
    }

    # Read attributes file
    with open(paths["attributes"]) as file:
        attributes = yaml.load(file, Loader=yaml.FullLoader)
    # Read gem5 config file
    with open(paths["m5out"] + "/config.json") as f:
        config = json.load(f)
    # Read gem5 stats file
    stats = {}
    with open(paths["m5out"] + "/stats.txt", "r") as file:
        pattern = re.compile(r"(\S+)\s+(\S+).*#")
        for line in file.readlines():
            match = pattern.match(line)
            if match:
                stats[match.group(1)] = match.group(2)

    # Process mappings
    print("\n----------------- Processing Mappings ------------------")
    arch = Arch(attributes, config)
    action_counts = ActionCounts(stats)
    for file in sorted(os.listdir(paths["mappings"])):
        path = os.path.join(paths["mappings"], file)
        base, ext = os.path.splitext(path)
        if os.path.isfile(path) and ext == ".py":
            module = __import__(base.replace("/", "."), fromlist=[""])
            processMappings(arch, action_counts, module, args.v)

    # Write architecture
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

    # Write action counts
    action_counts_yaml = {"action_counts": {
        "version": 0.3,
        "local": action_counts.get(),
    }}
    with open(paths["input"] + "/action_counts.yaml", "w") as file:
        yaml.dump(action_counts_yaml, file, sort_keys=False)

    # invoke accelergy
    accelergy_command = "accelergy -o " + paths["output"] + " " + paths["input"] + "/*.yaml " + " -v 1"
    print("\n---------------- Hand-off to Accelergy  ----------------")
    print(accelergy_command)
    print()
    if not args.d:
        os.system(accelergy_command)


def processMappings(arch, action_counts, module, verbose):
    print("Mapping class %s → %s" % (module.gem5_class, module.accelergy_class))
    if module.gem5_class in arch.instances:
        for instance in arch.instances[module.gem5_class]:
            param = arch.getParam(instance)
            add = module.criteria  # add is either boolean or a function
            if callable(module.criteria):
                add = module.criteria(param)
            if add:
                name = instance.split(".")[-1]
                if module.name_append != "":
                    name += "_" + module.name_append
                arch_path = module.path + "." + name
                print("    %s → %s" % (instance, arch_path))
                component = arch.addLocal(module.path, name, module.accelergy_class, module.gem5_class)
                for constant in module.constants:
                    if "attributes" not in component:
                        component["attributes"] = {}
                    component["attributes"][constant[0]] = constant[1]
                    if verbose:
                        print("        CONST    %s = %s" % (constant[0], constant[1]))
                for attribute in module.attributes:
                    try:
                        if callable(attribute[1]):
                            value = attribute[1](param)
                        else:
                            value = arch.getParamField(instance, attribute[1])
                    except KeyError:
                        value = None
                    if value is None:
                        print("        WARNING  cannot locate attribute %s of %s" % (attribute[1], instance))
                    else:
                        if "attributes" not in component:
                            component["attributes"] = {}
                        component["attributes"][attribute[0]] = value
                        if verbose:
                            print("        ATTR     %s = %s" % (attribute[0], value))
                for action in module.actions:
                    total_counts = 0
                    for action_name in action[1]:
                        total_counts += getActionCount(instance, action_name, action_counts)
                    if len(action) > 2:
                        for action_name in action[2]:
                            total_counts -= getActionCount(instance, action_name, action_counts)
                    action_counts.addField(arch_path, action[0], total_counts)
                    if verbose:
                        print("        ACTION   %s = %s" % (action[0], total_counts))


def getActionCount(instance, action_name, action_counts):
    counts = action_counts.getActionCounts(instance, action_name)
    if counts is None:
        counts = action_counts.getActionCounts("", action_name)
    if counts is None:
        print("        WARNING  cannot locate action count %s.%s" % (instance, action_name))
        counts = 0
    return counts


class Arch:
    def __init__(self, attributes, config):
        self.arch = {"name": "system", "attributes": {}}  # architecture tree
        self.config = config
        self.instances = {}  # instances of each gem5 class in config
        self.populateClassInstances(config["system"], "system")

        if "technology" not in attributes:
            raise Exception("Attribute technology not in attributes.yaml")
        self.arch["attributes"]["technology"] = attributes["technology"]
        if "datawidth" not in attributes:
            raise Exception("Attribute datawidth not in attributes.yaml")
        self.arch["attributes"]["datawidth"] = attributes["datawidth"]
        if "device_type" not in attributes:
            raise Exception("Attribute device_type not in attributes.yaml")
        self.arch["attributes"]["device_type"] = attributes["device_type"]
        clockrate = self.getParamField("system.clk_domain", "clock")
        if clockrate is None:
            raise Exception("Unable to parse clockrate at system.clk_domain.clock")
        clockrate = int(1e6/(float(clockrate))) # convert ps to MHz
        self.arch["attributes"]["clockrate"] = clockrate


    def populateClassInstances(self, source, path):
        if "type" in source:
            if source["type"] not in self.instances:
                self.instances[source["type"]] = []
            self.instances[source["type"]].append(path)
        for key, value in source.items():
            if type(value) == dict:
                self.populateClassInstances(value, path + "." + key)
            if type(value) == list and len(value) == 1 and type(value[0]) == dict:
                self.populateClassInstances(value[0], path + "." + key)

    def addLocal(self, path, name, accelergy_class, gem5_class):
        pathNames = path.split(".")
        if pathNames[0] == self.arch["name"]:
            component = self.arch
        else:
            raise Exception("Root component %s does not match" % pathNames[0])
        for pathName in pathNames[1:]:
            nextComponent = None
            if "subtree" in component:
                for c in component["subtree"]:
                    if c["name"] == pathName:
                        nextComponent = c
            else:
                component["subtree"] = []
            if nextComponent is None:
                nextComponent = {"name": pathName}
                component["subtree"].append(nextComponent)
            component = nextComponent
        if "local" not in component:
            component["local"] = []
        newComponent = {"name": name, "class": accelergy_class, "gem5_class": gem5_class}
        component["local"].append(newComponent)
        return newComponent

    def getParam(self, path):
        names = path.split(".")
        source = self.config
        for name in names:
            if name in source:
                source = source[name]
                if type(source) == list:
                    source = source[0]
            else:
                raise Exception("Unable to find source component" + path)
        return source

    def getParamField(self, path, field):
        source = self.getParam(path)
        names = field.split(".")
        for name in names[:-1]:
            if name in source:
                source = source[name]
                if type(source) == list:
                    source = source[0]
            else:
                return None
        if names[-1] in source:
            value = source[names[-1]]
            if type(value) == list and len(value) == 1:  # unwrap lists of length 1
                return value[0]
            else:
                return value
        else:
            return None


class ActionCounts:
    def __init__(self, stats):
        self.stats = stats
        self.action_map = {}

    def getActionCounts(self, source_path, source_name):
        if source_path == "":
            field = source_name
        else:
            field = source_path + "." + source_name
        if field in self.stats:
            return int(self.stats[field])
        else:
            return None

    def addField(self, arch_path, arch_name, counts):
        if arch_path not in self.action_map:
            self.action_map[arch_path] = []
        self.action_map[arch_path].append({"name": arch_name, "counts": counts})

    def get(self):
        action_counts = []
        for path, counts in self.action_map.items():
            action_counts.append({"name": path, "action_counts": counts})
        return action_counts


if __name__ == "__main__":
    if sys.version_info < (3, 0):
        print("Python 2.x is not supported for connector.py")
        sys.exit(1)
    main()
