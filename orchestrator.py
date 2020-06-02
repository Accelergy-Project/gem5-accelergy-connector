''' 
IMPORTANT: This file must be run as python3 otherwise encoding issues will
arise in the output files
'''

import os
import sys
import yaml
import json
import argparse
from yaml_handler import *
from fu_helper import *
from util_helper import *
from precise_attribute_collector import *

def main():
    # example calling this:
    # python3 orchestrator.py -m m5out -i example_input -o example_output -c example-connector-config.yaml
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

    # generate architecture description
    off_chip_mems, on_chip_caches, tlbs, fu_mappings = processArchitecture(paths)

    # generate action counts
    processActionCounts(paths, off_chip_mems, on_chip_caches, tlbs, fu_mappings)

    accelergy_command = "accelergy -o " + paths["output"] + " " + paths["input"] + "/*.yaml "  + "components/*.yaml -v 1"
    print("Accelergy command:", accelergy_command)
    os.system(accelergy_command)

def processArchitecture(paths):
    with open(paths["config"]) as file:
        config_info = yaml.load(file, Loader=yaml.FullLoader)

    # read in accelergy configuration
    with open(paths["m5out"] + "/config.json") as f:
        config_data = json.load(f)
    system_info = config_data["system"]
    cpu_info = system_info["cpu"]
    # collect the system level attributes we care about
    system_attributes = config_info["hardware_attributes"]
    system_attr_collector = PreciseAttributeCollector(
        {
            "clockrate": ["clk_domain", "clock"], # in MHz (Megahertz)
            "block_size": ["cache_line_size"],
            "vdd": ["clk_domain", "voltage_domain", "voltage"]
        }
    )
    system_attributes.update(system_attr_collector.get_attr_dict(system_info))

    # attributes that memory inherits from the system if not specified for the unit
    memory_units_inherit_system_attrs = ["technology", "block_size", "clockrate"]
    memory_units_inherit_attrs = {}
    for attr in memory_units_inherit_system_attrs:
        if attr in system_attributes:
            memory_units_inherit_attrs[attr] = system_attributes[attr]

    # collect the cpu level attributes we care about
    # attributes that cpu inherits from the system if not specified for the cpu
    cpu_attributes = {}
    cpu_inherit_system_attrs = ["datawidth", "technology", "clockrate", "vdd"]
    cpu_inherit_attrs = {}
    for attr in cpu_inherit_system_attrs:
        if attr in system_attributes:
            cpu_inherit_attrs[attr] = system_attributes[attr]
    cpu_attr_collector = PreciseAttributeCollector(
        {
            "number_hardware_threads": ["numThreads"]
        },
        cpu_inherit_attrs
    )
    cpu_attributes.update(cpu_attr_collector.get_attr_dict(cpu_info))

    # this is the path to our list of functional units within our CPU
    fu_path = []
    for fu_path_key, fu_path in config_info['fu_unit_cpu_path'].items():
        if checkIfPathExists(cpu_info, fu_path):
            print("Using fu_path labeled: " + str(fu_path_key))
            fu_path = fu_path
    fu_mappings = getFunctionalUnitsToOpSetMapping(cpu_info, fu_path)

    off_chip_compound_components, off_chip_mems = addOffChipComponents(config_info, system_info, memory_units_inherit_attrs)
    on_chip_compound_components, on_chip_caches, tlbs = addOnChipComponents(config_info, system_info, cpu_info, cpu_attributes, fu_mappings, memory_units_inherit_attrs)

    # yaml where I add the top level
    # this is initally just filled with boiler plate
    architecture_yaml = \
        {"architecture": {
            "version": 0.3,
            "subtree": [
                    {
                        "name": "system",
                        "attributes": system_attributes,
                        "local": off_chip_compound_components,
                        "subtree": [
                            {
                                "name": "chip",
                                "attributes": cpu_attributes,
                                "local":  on_chip_compound_components,
                            }
                        ]
                    }
                ]
            }
        }

    with open(paths["input"] + "/architecture.yaml", "w") as file:
        yaml.dump(architecture_yaml, file, sort_keys=False)

    return off_chip_mems, on_chip_caches, tlbs, fu_mappings

def addOffChipComponents(config_info, system_info, memory_units_inherit_attrs):
    off_chip_compound_components = []
    off_chip_mem_ctrl_types = config_info["type_to_class_names"]['off_chip_mem_ctrl']
    off_chip_mem_ctrl_to_mem_type = {}
    off_chip_mem_ctrl_other_attr_remap = {"memory_type": {}}
    for off_chip_mem_ctrl_type in off_chip_mem_ctrl_types:
        off_chip_mem_ctrl_to_mem_type[off_chip_mem_ctrl_type.lower()] = "memory_controller" # as per McPat
        off_chip_mem_ctrl_other_attr_remap["memory_type"][off_chip_mem_ctrl_type.lower()] = "main_memory"

    off_chip_mems_dict = getComponentsOfTypesDict(system_info, off_chip_mem_ctrl_types)
    off_chip_mems = [key for key in off_chip_mems_dict]
    print(off_chip_mems)
    off_chip_mem_attr_collector = PreciseAttributeCollector(
        {
            "class": ["type"],
            "memory_type": ["type"],
            "response_latency": ["tCL"],
            "size": ["device_size"],
            "page_size": ["device_rowbuffer_size"],
            "burst_length": ["burst_length"],
            "port": ["port", "peer", -2],
            "bus_width": ["device_bus_width"],
            "ranks_per_channel": ["ranks_per_channel"],
            "banks_per_rank": ["banks_per_rank"]
        },
        memory_units_inherit_attrs
    )
    print("Adding off chip memory units")
    off_chip_compound_components.extend(multipleComponentYamlData(off_chip_mems_dict, off_chip_mem_attr_collector, class_remap=off_chip_mem_ctrl_to_mem_type, other_attr_remap=off_chip_mem_ctrl_other_attr_remap))
    return off_chip_compound_components, off_chip_mems

def addOnChipComponents(config_info, system_info, cpu_info, cpu_attributes, fu_mappings, memory_units_inherit_attrs):
    on_chip_compound_components = []
    # I am tentatively treating all cache Components as on-chip, as it appears
    # that as of right now only the icache and dcache can be specified within the cpu,
    # thus the other caches are attributes of the entire system
    cache_types = config_info["type_to_class_names"]['cache']
    on_chip_caches_dict = getComponentsOfTypesDict(system_info, cache_types)
    on_chip_caches = [key for key in on_chip_caches_dict]
    print(on_chip_caches)
    cache_attr_collector = PreciseAttributeCollector(
        {
            "class": ["type"],
            "replacement_policy": ["replacement_policy", "type"],
            "associativity": ["assoc"],
            "tag_size": ["tags", "entry_size"],
            "block_size": ["tags", "block_size"],
            "tag_size": ["tags", "entry_size"],
            "write_buffers": ["write_buffers"],
            "size": ["size"],
            "mshrs": ["mshrs"],
            # "tag_latency": ["tag_latency"], McPat convert I am following did not use these
            # "data_latency": ["data_latency"], it instead just used hit_latency and resp_latency
            "hit_latency": ["hit_latency"],
            "response_latency": ["response_latency"],
            # "network_cpu_side": ["cpu_side", "peer", -2], Doesn't look like these are needed
            # "network_mem_side": ["mem_side", "peer", -2]
        },
        memory_units_inherit_attrs
    )
    # on_chip_compound_components.extend(cacheComponentsYamlData(caches_dict))
    print("Adding caches")
    on_chip_compound_components.extend(multipleComponentYamlData(on_chip_caches_dict, cache_attr_collector, add_name_as_attr="cache_type"))

    mem_bus_types = config_info["type_to_class_names"]['mem_bus']
    buses_dict = getComponentsOfTypesDict(system_info, mem_bus_types)
    bus_attr_collector = PreciseAttributeCollector(
        {
            "class": ["type"],
            "response_latency": ["response_latency"],
            "protocol_response_latency": ["snoop_filter", "lookup_latency"],
            "width": ["width"]
        }
    )
    print("Adding buses")
    on_chip_compound_components.extend(multipleComponentYamlData(buses_dict, bus_attr_collector))

    # now get the attributes of specific sub components of the cpu
    decode_attr_collector = PreciseAttributeCollector(
        {
            "instr_buffer_size": ["decodeInputBufferSize"],
            "instr_width": ["decodeInputWidth"],
            "cycle_delay": ["decodeToExecuteForwardDelay"]
        }
    )
    print("Adding decode")
    on_chip_compound_components.append(singleComponentYamlData(cpu_info, decode_attr_collector, "decode"))

    fetch_attr_collector = PreciseAttributeCollector(
        {
            "ports": ["fetch1FetchLimit"],
        }
    )
    print("Adding fetch")
    on_chip_compound_components.append(singleComponentYamlData(cpu_info, fetch_attr_collector, "fetch"))

    # Add TLBs (Translation Lookup Buffers), should typically be itlb, dtlb,
    # seem to be referenced in gem5 as itb, dtb
    tlb_types = config_info["type_to_class_names"]['tlb']
    tlbs_dict = getComponentsOfTypesDict(cpu_info, tlb_types)
    tlbs = [key for key in tlbs_dict]
    tlb_attr_collector = PreciseAttributeCollector(
        {
            "number_entries": ["size"]
        }
    )
    print("Adding tlbs")
    on_chip_compound_components.extend(multipleComponentYamlData(tlbs_dict, tlb_attr_collector, component_class="tlb"))

    # Add in functional units
    # What I need to fetch from functional units:
    #   opClasses so I can track down action counts in the stats
    # Right now I just fetch their names and map them to a McPat fu type (ie ALU, FPU, MUL)
    # later on opClasses could be an actual class with more data ie: latency
    # or other user specified inputs that could be used, however McPat doesn't seem to use these

    # calculate the number of each type of functional unit for config
    num_alu_units = len(fu_mappings["ALU_units"])
    num_mul_units = len(fu_mappings["MUL_units"])
    num_fpu_units = len(fu_mappings["FPU_units"])

    # Now adding the execution unit, it is likely that special code will be required here
    # to not only create the execution unit but link relevant sub components
    # attributes that exec inherits from the system if not specified for the unit
    exec_unit_inherit_cpu_attrs = ["datawidth", "technology", "clockrate"]
    exec_unit_inherit_attrs = {}
    for attr in exec_unit_inherit_cpu_attrs:
        if attr in cpu_attributes:
            exec_unit_inherit_attrs[attr] = cpu_attributes[attr]
    exec_attr_collector = PreciseAttributeCollector(
        {
            "instruction_buffer_size": ["executeInputBufferSize"],
            "issue_width": ["executeIssueLimit"],
            "commit_width": ["executeCommitLimit"],
            "store_buffer_size": ["executeLSQMaxStoreBufferStoresPerCycle"],
            "prediction_width": ["branchPred", "numThreads"] # this stat is for branch predicition, might move later
                                                             # might need to make this it's own component
        },
        exec_unit_inherit_attrs
    )
    exec_additional_attributes = {
        "alu_units": num_alu_units,
        "mul_units": num_mul_units,
        "fpu_units": num_fpu_units
    }
    print("Adding exec")
    on_chip_compound_components.append(singleComponentYamlData(cpu_info, exec_attr_collector, "exec", additional_attributes=exec_additional_attributes))
    return on_chip_compound_components, on_chip_caches, tlbs

def processActionCounts(paths, off_chip_mems, on_chip_caches, tlbs, fu_mappings):
    # read in accelergy stats
    stat_lines = []
    with open(paths["m5out"] + "/stats.txt") as f:
        stat_lines = f.readlines()
        stat_lines = [stat_line.split() for stat_line in stat_lines]

    actionCountYAMLs = []

    # Get decode action acounts
    # *** This can't be done for minorCPU, likely as the data is not collected due to simplifications
    #     so will need to add it for O3CPU as that will have clearer actions likely

    # Get fetch action counts
    # **# This stage is also ambiguous atm

    # Get the off chip memory action counts from names in off_chip_mems
    off_chip_memory_action_name_to_fetch_to_stat_names = {
        # "accesses": [""], # Don't worry about this for now as not clear waht this is in gem5 stats.txt
        #                     worst case it can probably be derived but it'd be better if we could extract
        #                     the exact number, probably need a better workload
        "read_access": [".num_reads::total"],
        "write_access": [".num_writes::total"] # this is speculation, don't see it in minorCPU or O3 CPU
    }
    off_chip_mem_name_to_full_path_name = {}
    for mem_name in off_chip_mems:
        off_chip_mem_name_to_full_path_name[mem_name] = "system." + mem_name

    print("Adding off chip mem action counts")
    actionCountYAMLs.extend(getActionCountsYAMLsForComponentsFromStats(off_chip_mem_name_to_full_path_name, off_chip_memory_action_name_to_fetch_to_stat_names, stat_lines))

    # Get the cache action counts from on_chip_caches
    on_chip_memory_action_name_to_fetch_to_stat_names = {
        "read_access": [".ReadReq_hits::total"],
        "read_miss": [".ReadReq_misses::total"],
        "write_access": [".WriteReq_hits::total"],
        "write_miss": [".WriteReq_misses::total"]
    }
    on_chip_caches_name_to_full_path_name = {}
    for cache_name in on_chip_caches:
        on_chip_caches_name_to_full_path_name[cache_name] = "system.chip." + cache_name
    print("Adding on chip cache action counts")
    actionCountYAMLs.extend(getActionCountsYAMLsForComponentsFromStats(on_chip_caches_name_to_full_path_name, on_chip_memory_action_name_to_fetch_to_stat_names, stat_lines))

    # get the operations for each type of fu based on their ops present
    ALU_ops = mergeDictSetValuesForKeys(fu_mappings["ALU_units"])
    MUL_ops = mergeDictSetValuesForKeys(fu_mappings["MUL_units"])
    FPU_ops = mergeDictSetValuesForKeys(fu_mappings["FPU_units"])

    # Get the exec stage action counts
    # simply search the file for name matches to the operations
    # if there are multiple matches take the maximum value
    #   ***this occurs in O3CPU when there is an instruction queue issue count and a commit count
    #       thus max will be the most accurate value in terms of energy consumption
    ALU_instructions_executed = getFuncUnitOpsExecutedInStats(ALU_ops, stat_lines)
    MUL_instructions_executed = getFuncUnitOpsExecutedInStats(MUL_ops, stat_lines)
    FPU_instructions_executed = getFuncUnitOpsExecutedInStats(FPU_ops, stat_lines)
    exec_action_name_to_count = {
        "int_instruction": ALU_instructions_executed,
        "mul_instruction": MUL_instructions_executed,
        "fp_instruction": FPU_instructions_executed
    }
    exec_component_full_path_name = "system..chip.exec"
    print("Adding exec action counts")
    actionCountYAMLs.append(createYAMLActionCountComponent(exec_component_full_path_name, exec_action_name_to_count))

    # Get TLB data for dtb, itb, and any other cpu tlbs from tlbs
    tlb_action_name_to_fetch_to_stat_names = {
        "read_access": [".read_accesses"],
        # "read_hit": [".read_hits"],
        # "read_miss": [".read_misses"],
        "write_access": [".write_accesses"]
        # "write_hit": [".write_hits"],
        # "write_miss": [".write_misses"],
        # "total_access": [".accesses"],
        # "total_hit": [".hits"],
        # "total_miss": [".misses"]
    }
    tlb_name_to_full_path_name = {}
    for tlb in tlbs:
        tlb_name_to_full_path_name[tlb] = "system.chip." + tlb
    print("Adding tlb action counts")
    actionCountYAMLs.extend(getActionCountsYAMLsForComponentsFromStats(tlb_name_to_full_path_name, tlb_action_name_to_fetch_to_stat_names, stat_lines))

    # yaml where I add the top level
    # this is initally just filled with boiler plate
    action_counts_yaml = {"action_counts": {
                            "version": 0.3,
                            "local": actionCountYAMLs
                            }
                        }

    accelergy_action_counts_file_name = paths["input"] +  "/action_counts.yaml"
    with open(accelergy_action_counts_file_name, "w") as file:
        yaml.dump(action_counts_yaml, file, sort_keys=False)

if __name__== "__main__":
    main()
