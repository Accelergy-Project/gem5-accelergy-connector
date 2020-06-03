import os
import sys
import yaml
import json
import argparse
from arch import Arch


def main():
    # python3 orchestrator.py -m example/m5out -i example/input -o example/output -c example/config.yaml
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", help="the gem5 m5out directory path", required=True)
    parser.add_argument("-i", help="the directory path to put the accelergy input", required=True)
    parser.add_argument("-o", help="the directory path to put the accelergy output", required=True)
    parser.add_argument("-c", help="the config file for this converter", required=True)
    args = parser.parse_args()
    paths = {
        "m5out": args.m,
        "input": args.i,
        "output": args.o,
        "config": args.c,
    }

    arch = processArch(paths)         # generate architecture description
    processActionCounts(paths, arch)  # generate action counts

    accelergy_command = "accelergy -o " + paths["output"] + " " + paths["input"] + "/*.yaml " + "components/*.yaml -v 1"
    print("Accelergy command:", accelergy_command)
    # FIXME re-enable after refactor
    # os.system(accelergy_command)


def processArch(paths):
    # read connector configuration file
    with open(paths["config"]) as file:
        connector_config = yaml.load(file, Loader=yaml.FullLoader)
    # read gem5 source architecture configuration file
    with open(paths["m5out"] + "/config.json") as f:
        source_config = json.load(f)

    arch = Arch(connector_config, source_config)

    # system attributes
    arch.addSystemAttr("technology")
    arch.addSystemAttr("datawidth")
    arch.addSourceAttr("system", "clockrate", "system.clk_domain", "clock")
    arch.addSourceAttr("system", "block_size", "system", "cache_line_size")
    arch.addSourceAttr("system", "vdd", "system.clk_domain.voltage_domain", "voltage")

    # chip attributes
    arch.addSubtree("system", "chip")
    arch.addSourceAttr("system.chip", "number_hardware_threads", "system.cpu", "numThreads")

    populateArch(arch)
    arch_yaml = {
        "architecture": {
            "version": 0.3,
            "subtree": arch.arch
        }
    }
    with open(paths["input"] + "/architecture.yaml", "w") as file:
        yaml.dump(arch_yaml, file, sort_keys=False)
    return arch


def populateArch(arch):
    # add memory controllers
    addComponents(arch, "system", "memory_controller", [
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
    addComponents(arch, "system.chip", "cache", [], [
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
    addComponents(arch, "system.chip", "coherentxbar", [], [
        ("response_latency", "response_latency"),
        ("protocol_response_latency", "snoop_filter.lookup_latency"),
        ("width", "width"),
    ])

    # add TLBs
    addComponents(arch, "system.chip", "tlb", [], [
        ("number_entries", "size"),
    ])

    # add exec
    gemCPU = arch.classMap["cpu"]
    if gemCPU in arch.classInstances and len(arch.classInstances[gemCPU]) == 1:
        cpu = arch.classInstances[gemCPU][0]
    else:
        raise Exception("Unable to locate cpu " + gemCPU)
    addComponents(arch, "system.chip", "exec", [
        ("instruction_buffer_size", arch.getSourceField(cpu + ".executeInputBufferSize")),
        ("issue_width", arch.getSourceField(cpu + ".executeIssueLimit")),
        ("commit_width", arch.getSourceField(cpu + ".executeCommitLimit")),
        ("store_buffer_size", arch.getSourceField(cpu + ".executeLSQStoreBufferSize")),
        ("prediction_width", arch.getSourceField(cpu + ".branchPred.numThreads")),
    ], [])


def addComponents(arch, path, accelergyClass, staticAttr, sourceAttr, dynamicAttr=()):
    gemClass = arch.classMap[accelergyClass]
    components = arch.classInstances[gemClass] if gemClass in arch.classInstances else []
    for component in components:
        name = component.split(".")[-1]
        arch.addLocal(path, name, accelergyClass)
        fullName = path + "." + name
        for attr in staticAttr:
            arch.addAttr(fullName, attr[0], attr[1])
        for attr in sourceAttr:
            arch.addSourceAttr(fullName, attr[0], component, attr[1])
        if dynamicAttr:
            params = arch.getSource(component)
            for attr in dynamicAttr:
                arch.addAttr(fullName, attr[0], attr[1](params))

        # update component map
        if accelergyClass not in arch.archMap:
            arch.archMap[accelergyClass] = {}
        arch.archMap[accelergyClass][fullName] = component

    # print diagnostics
    print("gem5-accelergy-connector:",
          gemClass, "->", accelergyClass)
    if accelergyClass in arch.archMap:
        for key, value in arch.archMap[accelergyClass].items():
            print("\t", value, "->", key)
    else:
        print("\t NO MATCHES FOUND")


def processActionCounts(paths, arch):
    action_counts_yaml = {"action_counts": {
        "version": 0.3,
        "local": []
    }}
    with open(paths["input"] + "/action_counts.yaml", "w") as file:
        yaml.dump(action_counts_yaml, file, sort_keys=False)


if __name__ == "__main__":
    if sys.version_info < (3, 0):
        print("Python 2.x is not supported for orchestrator.py")
        sys.exit(1)
    main()
