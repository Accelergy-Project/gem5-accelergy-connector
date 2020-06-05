import os
import re
import sys
import yaml
import json
import argparse
from arch import *
from action_counts import *


def main():
    # python3 orchestrator.py -m example/m5out -i example/input -o example/output -c example/config.yaml
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


if __name__ == "__main__":
    if sys.version_info < (3, 0):
        print("Python 2.x is not supported for orchestrator.py")
        sys.exit(1)
    main()
