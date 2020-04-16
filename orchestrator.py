''' 
IMPORTANT
This file must be run as python3 otherwise encoding issues will arise in the output files
'''
import os
import sys
import yaml
import json

def printStats(cpu_general_stats, memory_access_stats, cpu_op_stats):
    print("**********General stats**********")
    stat_names = [stat for stat in cpu_general_stats]
    stat_names.sort()
    for stat in stat_names:
        print(stat + ":" + str(cpu_general_stats[stat]))
    print("**********Memory Access Stats**********")
    for stat in memory_access_stats:
        print(stat + ":" + str(memory_access_stats[stat]))
    print("**********Operation stats**********")
    op_names = [op for op in cpu_op_stats]
    op_names.sort()
    for op in op_names:
        print(op + ":" + str(cpu_op_stats[op]))

def getComponentsOfTypesDict(info_dict, types):
    caches_dict = {}
    for sub_component_key in info_dict:
        if isinstance(info_dict[sub_component_key], dict) and \
              "type" in info_dict[sub_component_key] and \
              info_dict[sub_component_key]["type"] in types:
           caches_dict[sub_component_key] = info_dict[sub_component_key]
        elif isinstance(info_dict[sub_component_key], dict):
            caches_dict.update(getComponentsOfTypesDict(info_dict[sub_component_key], types))
    return caches_dict

def multipleComponentYamlData(components_dict, attr_collector, component_class="",
                              class_remap={}, other_attr_remap={}):
    '''
    Get the YAML format for a list of components
    '''
    yaml_components = []
    for component in components_dict:
        yaml_component = singleComponentYamlData(components_dict[component], attr_collector, component,
                                                 component_class=component_class, class_remap=class_remap,
                                                 other_attr_remap=other_attr_remap)
        yaml_components.append(yaml_component)
    return yaml_components

def singleComponentYamlData(component_dict, attr_collector, component_name,
                            component_class="", class_remap={}, other_attr_remap={},
                            additional_attributes={}):
    '''
    Get the YAML format for a single component
    '''
    if component_class == "":
        component_class = component_name
    attributes = {}
    attributes.update(additional_attributes)
    collected_attributes = attr_collector.get_attr_dict(component_dict)
    attributes.update(collected_attributes)
    # handle remapping the 
    if "class" in attributes:
        component_class = attributes.pop('class', 'Class Not Found')
        if component_class in class_remap:
            component_class = class_remap[component_class]
        component_class = component_class.lower()
    for attr in attributes:
        if attr in other_attr_remap:
            value = attributes[attr]
            attr_remap_dict = other_attr_remap[attr]
            if value in attr_remap_dict:
                attributes[attr] = attr_remap_dict[value] 

    full_yaml_component = {"name": component_name, "class": component_class, "attributes": attributes}
    # print(full_yaml_component)
    return full_yaml_component


class PreciseAttributeCollector:
    # this attribute collector looks for exact matches of attribute names
    def __init__(self, attr_to_path, inherit_attr={}):
        self.attr_to_path = attr_to_path
        self.inherit_attr = inherit_attr

    def get_attr_dict(self, info_dict):
        attr_dict = {}
        for attr, attr_path in self.attr_to_path.items():
            attr_value = self.recursive_find_attr(attr_path, info_dict)
            if attr_value != None:
                attr_value = attr_value.lower() if isinstance(attr_value, str) else attr_value
                attr_dict[attr] = attr_value
        for attr, inherit_value in self.inherit_attr.items():
            if attr not in attr_dict:
                attr_dict[attr] = inherit_value
        return attr_dict


    def recursive_find_attr(self, path, info_dict):
        # base cases
        if len(path) == 1:
            if path[0] in info_dict:
                # this is to handle the case of returning the first element in a list
                if isinstance(info_dict[path[0]], list):
                    return info_dict[path[0]][0]
                return info_dict[path[0]]
            return None
        elif len(path) == 2 and isinstance(path[1], int):
            # this is used to get a subset of a path:
            # ie: "system.l2bus.slave[1]"
            # if we want l2bus (or the equivelant on all such paths) the int value is -2
            if path[0] in info_dict:
                full_path = info_dict[path[0]]
                split_path = full_path.split(".")
                neg_attr_index = path[1]
                if len(split_path) > -(path[1]):
                    return split_path[neg_attr_index]
            return None
        else: # recursive case
            if path[0] in info_dict:
                return self.recursive_find_attr(path[1:], info_dict[path[0]])
            else:
                return None

def getActionCountsYAMLsForComponentsFromStats(components_to_full_component_path_name, attributes_to_stat_names, stat_lines):
    component_to_action_name_to_count = {}
    for component, full_component_name in components_to_full_component_path_name.items():
        component_to_action_name_to_count[full_component_name] = {}

    for stat_line in stat_lines:
            # check if op in stat_line and if the stat_line contains a numerical value
            # which goes second in gem5 when a line is split by whitespace, this is the case if len > 1
            # from observation
            if len(stat_line) < 2:
                continue
            try:
                value = int(stat_line[1])
            except ValueError:
                # this must not be a data line
                continue
            matchFound = False
            for component, full_component_name in components_to_full_component_path_name.items():
                for attr, valid_stat_names in attributes_to_stat_names.items():
                    if attr in component_to_action_name_to_count[full_component_name]:
                        continue # this means we already found this attribute elsewhere
                    for valid_stat_name in valid_stat_names: 
                        if component in stat_line[0] and valid_stat_name in stat_line[0]:
                            component_to_action_name_to_count[full_component_name][attr] = value
                            break
                    if matchFound:
                        break
                if matchFound:
                    break

    action_count_yamls = []
    for component in component_to_action_name_to_count:
        if len(component_to_action_name_to_count[component]) > 0: # if this == 0 then it has no actions so skip
            action_count_yamls.append(createYAMLActionCountComponent(component, component_to_action_name_to_count[component]))

    print(component_to_action_name_to_count)
    return action_count_yamls

# will need to eventually add support for arguments
def createYAMLActionCountComponent(name, action_name_to_count):
    yaml_component = {}
    yaml_component["name"] = name
    action_counts = []
    for action, count in action_name_to_count.items():
        new_action_count = {}
        new_action_count["name"] = action
        new_action_count["counts"] = count
        action_counts.append(new_action_count)
    yaml_component["action_counts"] = action_counts
    print(yaml_component)
    return yaml_component


def getFunctionalUnitsToOpSetMapping(cpu_info, fu_path, fu_num_prefix, counts_included=False):
    current_info = cpu_info
    for i in range(len(fu_path)):
        path_component_found = fu_path[i] in current_info
        if path_component_found:
            current_info = current_info[fu_path[i]]
        else:
            # return empty dict, no need to do more computation as we will
            # find nothing if we don't have the fu list
            print("Could not find fu with path provided, couldn't find path component: " + fu_path[i])
            return {}
    fu_units = current_info

    fu_to_op_mapping = {}
    for fu in fu_units:
        fu_name = fu["name"]
        if fu_num_prefix not in fu_name:
            print("Error with getting fu num, prefix of: " + fu_num_prefix + " not present in name: " + fu_name)
        fu_num = int(fu_name[len(fu_num_prefix):])
        ops = recursivelyFindAttributeValues(fu, ["opClass"])
        op_set = set(ops)
        fu_to_op_mapping[fu_num] = op_set

    return fu_to_op_mapping

def mergeDictSetValuesForKeys(key_to_list_dict, keys_to_merge):
    merged_values = set()
    for key in keys_to_merge:
        merged_values = merged_values.union(key_to_list_dict[key])
    return merged_values

def recursivelyFindAttributeValues(info, attributes_to_find):
    '''
    Returns a list of values that are mapped to by any attributes within
    attributes_to_find, searches recursively within info to find these values
    info can be a dict or list
    '''
    attribute_values = []
    if isinstance(info, dict):
        for key in info:
            if key in attributes_to_find:
                attribute_values.append(info[key])
            else:
                attribute_values.extend(recursivelyFindAttributeValues(info[key], attributes_to_find))
    elif isinstance(info, list):
        for sub_info in info:
            attribute_values.extend(recursivelyFindAttributeValues(sub_info, attributes_to_find))
    return attribute_values

def getFuncUnitOpsExecutedInStats(ops, stat_lines):
    instructions_executed = 0
    for op in ops:
        max_value = 0
        for stat_line in stat_lines:
            # check if op in stat_line and if the stat_line contains a numerical value
            # which goes second in gem5 when a line is split by whitespace
            if len(stat_line) > 1 and op in stat_line[0]:
                new_value = int(stat_line[1])
                max_value = new_value if new_value > max_value else max_value
        instructions_executed += max_value
    return instructions_executed

if __name__== "__main__":
    # if (len(sys.argv) < 6):
    #     print("Must provide all 5 arguments:")
    #     print("gem5 build full path, ex: /home/ubuntu/gem5/build/X86/gem5.opt")
    #     print("gem5 test configuration file full path, ex: /home/ubuntu/testConfigs/simple.py")
    #     print("accelergy input directory to put action counts under name action_counts.yaml full path")
    # gem5_build_path = sys.argv[1]
    # gem5_test_config = sys.argv[2]

    gem5_build_path = "/home/ubuntu/gem5/build/RISCV/gem5.opt"
    gem5_test_config = "/home/ubuntu/testConfigs/two_level.py"
    # Run the command to run our architecture on our designated workload
    gem5_command = gem5_build_path + " " + gem5_test_config
    os.system(gem5_command)

    accelergy_input_dir = "/home/ubuntu/five_stage_pipeline_components/five_stage_pipeline/input"
    accelergy_action_counts_file_name = "action_counts.yaml"
    accelergy_architecture_name = "minor_cpu_system_arch"

    # read in accelergy configuration
    with open("m5out/config.json") as f:
        config_data = json.load(f)
    system_info = config_data["system"]
    cpu_info = system_info["cpu"]

    input_dir = "/home/ubuntu/gem5toAcclergyOrchestration/input"
    components_dir = "/home/ubuntu/gem5toAcclergyOrchestration/input/components"
    # os.system("rm -r " + input_dir)

    # TODO, find where datawidth is specified, I can't immediately tell where,
    # my theory is it is a architecture attribute rather than MinorCPU or O3CPU
    # specifying it, not sure it is even specifiable
    system_attributes = {"technology": "45nm", "datawidth": 32}
    cpu_attributes = {}
    on_chip_compound_components = []
    off_chip_compound_components = []

    cache_types = ["Cache"]
    off_chip_mem_ctrl_types = ["DRAMCtrl"]
    off_chip_mem_ctrl_to_mem_type = {"dramctrl": "memory_controller"} # as per McPat
    off_chip_mem_ctrl_other_attr_remap = {
        "cache_type": {
            "dramctrl": "main_memory"
        }
    }
    mem_bus_types = ["CoherentXBar"]
    tlb_types = ["RiscvTLB"] # need to add other ISAs later

    # collect the system level attributes we care about
    system_attr_collector = PreciseAttributeCollector(
        {
            "clock": ["clk_domain", "clock"], # in MHz (Megahertz)
            "block_size": ["cache_line_size"],
            "vdd": ["clk_domain", "voltage_domain", "voltage"]
        }
    )
    system_attributes.update(system_attr_collector.get_attr_dict(system_info))
    # collect the cpu level attributes we care about
    # attributes that cpu inherits from the system if not specified for the cpu
    cpu_inherit_system_attrs = ["datawidth", "technology"]
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

    # attributes that memory inherits from the system if not specified for the unit
    memory_units_inherit_system_attrs = ["technology", "block_size"]
    memory_units_inherit_attrs = {}
    for attr in memory_units_inherit_system_attrs:
        if attr in system_attributes:
            memory_units_inherit_attrs[attr] = system_attributes[attr]

    off_chip_mems_dict = getComponentsOfTypesDict(system_info, off_chip_mem_ctrl_types)
    off_chip_mems = [key for key in off_chip_mems_dict]
    print(off_chip_mems)
    off_chip_mem_attr_collector = PreciseAttributeCollector(
        {
            "class": ["type"],
            "cache_type": ["type"],
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

    # I am tentatively treating all cache Components as on-chip, as it appears
    # that as of right now only the icache and dcache can be specified within the cpu,
    # thus the other caches are attributes of the entire system
    on_chip_caches_dict = getComponentsOfTypesDict(system_info, cache_types)
    on_chip_caches = [key for key in on_chip_caches_dict]
    print(on_chip_caches)
    cache_attr_collector = PreciseAttributeCollector(
        {
            "class": ["type"],
            "cache_type": ["type"],
            "replacement_policy": ["replacement_policy", "type"],
            "associativity": ["assoc"],
            "tag_size": ["tags", "entry_size"],
            "block_size": ["tags", "block_size"],
            "tag_size": ["tags", "entry_size"],
            "write_buffers": ["write_buffers"],
            "size": ["size"],
            "tag_latency": ["tag_latency"],
            "data_latency": ["data_latency"],
            "network_cpu_side": ["cpu_side", "peer", -2],
            "network_mem_side": ["mem_side", "peer", -2]
        },
        memory_units_inherit_attrs
    )
    # on_chip_compound_components.extend(cacheComponentsYamlData(caches_dict))
    print("Adding caches")
    on_chip_compound_components.extend(multipleComponentYamlData(on_chip_caches_dict, cache_attr_collector))

    buses_dict = getComponentsOfTypesDict(system_info, mem_bus_types)
    bus_attr_collector = PreciseAttributeCollector(
        {
            "class": ["type"],
            "type": ["type"],
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
    # this also consists of making a exec compound component
    # I should force the user, who wrote the gem5 config to specify type for the
    # functional units they provide to gem5, they may omit entries
    # if there is not a clear match up to ALU, FPU, or MUL
    # they may also map multiple entries to the same unit
    # ie: 2 separate mul and div units could be combined into a MUL unit
    
    # # this is the path to our list of functional units within our CPU
    fu_path = ["executeFuncUnits", "funcUnits"]
    fu_num_prefix = "funcUnits"

    # What I need to fetch from functional units:
    #   opClasses
    # Best idea might be to map funcUnit number to list of opClasses right now
    # later on opClasses could be an actual class with more data ie: latency
    # or other user specified inputs that could be used
    fu_to_op_set_mapping = getFunctionalUnitsToOpSetMapping(cpu_info, fu_path, fu_num_prefix)
    # print(fu_to_op_mapping)

    num_alu_units = 2
    num_mul_units = 1
    num_fpu_units = 1
    # these don't necessarily need to match up with length of the following lists
    # ex: funcUnit2 might do mul and funcUnit3 might div, so together they make
    #     one MUL unit
    ALU_units = [0, 1]
    MUL_units = [2, 3]
    FPU_units = [4]

    ALU_ops = mergeDictSetValuesForKeys(fu_to_op_set_mapping, ALU_units)
    MUL_ops = mergeDictSetValuesForKeys(fu_to_op_set_mapping, MUL_units)
    FPU_ops = mergeDictSetValuesForKeys(fu_to_op_set_mapping, FPU_units)

    # Now adding the execution unit, it is likely that special code will be required here
    # to not only create the execution unit but link relevant sub components
    # attributes that exec inherits from the system if not specified for the unit
    exec_unit_inherit_cpu_attrs = ["datawidth", "technology"]
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

    # yaml where I add the top level 
    # this is initally just filled with boiler plate
    architecture_yaml = {"architecture": {
                            "version": 0.3,
                            "subtree": [
                                    {
                                        "name": accelergy_architecture_name,
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


    with open(input_dir + "/architecture.yaml", "w") as file:
        # noalias_dumper = yaml.dumper.SafeDumper
        # noalias_dumper.ignore_aliases = lambda self, data: True
        # yaml.dump(architecture_yaml, file, sort_keys=False, default_flow_style=False, Dumper=noalias_dumper)
        yaml.dump(architecture_yaml, file, sort_keys=False)


    ######################## Now to get action counts #############################
    # read in accelergy stats
    stat_lines = []
    with open("m5out/stats.txt") as f:
        stat_lines = f.readlines()
        stat_lines = [stat_line.split() for stat_line in stat_lines]

    actionCountYAMLs = []

    # Get decode action acounts
    # *** This can't be done for minorCPU, likely as the data is not collected due to simplifications
    #     so will need to add it for O3CPU

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
        off_chip_mem_name_to_full_path_name[mem_name] = accelergy_architecture_name + "." + mem_name

    print("Adding off chip mem action counts")
    actionCountYAMLs.extend(getActionCountsYAMLsForComponentsFromStats(off_chip_mem_name_to_full_path_name, off_chip_memory_action_name_to_fetch_to_stat_names, stat_lines))

    # Get the cache action counts from on_chip_caches
    # From McPat looks like we want the follwoing
    # <stat name="read_accesses" value="11824"/>
    # <stat name="write_accesses" value="11276"/>
    # <stat name="read_misses" value="1632"/>
    # <stat name="write_misses" value="183"/>
    on_chip_memory_action_name_to_fetch_to_stat_names = {
        "read_access": [".ReadReq_accesses::total"],
        # "read_hit": [".ReadReq_hits::total"],
        # "read_miss": [".ReadReq_misses::total"],
        "write_access": [".WriteReq_accesses::total"]
        # "write_hit": [".WriteReq_hits::total"],
        # "write_miss": [".WriteReq_misses::total"],
        # "total_access": [".overall_accesses::total"], # minorCPU l2cache only had totals
        # "total_hit": [".overall_hits::total"],
        # "total_miss": [".overall_misses::total"]
    }
    on_chip_caches_name_to_full_path_name = {}
    for cache_name in on_chip_caches:
        on_chip_caches_name_to_full_path_name[cache_name] = accelergy_architecture_name + ".chip." + cache_name
    print("Adding on chip cache action counts")
    actionCountYAMLs.extend(getActionCountsYAMLsForComponentsFromStats(on_chip_caches_name_to_full_path_name, on_chip_memory_action_name_to_fetch_to_stat_names, stat_lines))

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
    exec_component_full_path_name = accelergy_architecture_name + ".chip.exec"
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
        tlb_name_to_full_path_name[tlb] = accelergy_architecture_name + ".chip." + tlb
    print("Adding tlb action counts")
    actionCountYAMLs.extend(getActionCountsYAMLsForComponentsFromStats(tlb_name_to_full_path_name, tlb_action_name_to_fetch_to_stat_names, stat_lines))


    # yaml where I add the top level 
    # this is initally just filled with boiler plate
    action_counts_yaml = {"action_counts": {
                            "version": 0.3,
                            "local": actionCountYAMLs
                            }
                        }

    with open(input_dir + "/action_counts.yaml", "w") as file:
        # noalias_dumper = yaml.dumper.SafeDumper
        # noalias_dumper.ignore_aliases = lambda self, data: True
        # yaml.dump(architecture_yaml, file, sort_keys=False, default_flow_style=False, Dumper=noalias_dumper)
        yaml.dump(action_counts_yaml, file, sort_keys=False)

    # will need to change this with the proper directories/files when the time comes
    # os.chdir("/home/ubuntu/five_stage_pipeline_components/five_stage_pipeline/input")
    # os.system("3")







