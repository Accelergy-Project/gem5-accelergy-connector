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
    print(full_yaml_component)
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
        # base case
        if len(path) == 1:
            if path[0] in info_dict:
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


def getFunctionalUnitsToOpsMapping(cpu_info, fu_path, fu_num_prefix, counts_included=False):
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
        fu_to_op_mapping[fu_num] = ops

    return fu_to_op_mapping

def mergeDictListValues(key_to_list_dict, keys_to_merge):
    merged_list = []
    for key in keys_to_merge:
        merged_list.extend(key_to_list_dict[key])
    return merged_list

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

# def createCompoundComponent(path, attributes, )

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

    input_dir = "/home/ubuntu/input"
    components_dir = "/home/ubuntu/input/components"
    # os.system("rm -r " + input_dir)

    system_attributes = {"technology": "45nm"}
    cpu_attributes = {}
    on_chip_compound_components = []
    off_chip_compound_components = []

    cache_types = ["Cache"]
    off_chip_mem_ctrl_types = ["DRAMCtrl"]
    off_chip_mem_ctrl_to_mem_type = {"dramctrl": "dram"}
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
            "block_size": ["cache_line_size"]
        }
    )
    system_attributes.update(system_attr_collector.get_attr_dict(system_info))
    # collect the cpu level attributes we care about
    cpu_attr_collector = PreciseAttributeCollector(
        {
            "number_hardware_threads": ["numThreads"]
        }
    )
    cpu_attributes.update(cpu_attr_collector.get_attr_dict(cpu_info))

    # attributes that memory inherits from the system if not specified for the unit
    memory_units_inherit_system_attrs = ["block_size"]
    memory_units_inherit_attrs = {}
    for attr in memory_units_inherit_system_attrs:
        if attr in system_attributes:
            memory_units_inherit_attrs[attr] = system_attributes[attr]

    # I am tentatively treating all cache Components as on-chip, as it appears
    # that as of right now only the icache and dcache can be specified within the cpu,
    # thus the other caches are attributes of the entire system
    caches_dict = getComponentsOfTypesDict(system_info, cache_types)
    cache_attr_collector = PreciseAttributeCollector(
        {
            "class": ["type"],
            "cache_type": ["type"],
            "replacement_policy": ["replacement_policy", "type"],
            "associativity": ["assoc"],
            "tag_size": ["tags", "entry_size"],
            "block_size": ["tags", "block_size"],
            "write_buffers": ["write_buffers"],
            "size": ["size"],
            "network_cpu_side": ["cpu_side", "peer", -2],
            "network_mem_side": ["mem_side", "peer", -2]
        },
        memory_units_inherit_attrs
    )
    # on_chip_compound_components.extend(cacheComponentsYamlData(caches_dict))
    print("Adding caches")
    on_chip_compound_components.extend(multipleComponentYamlData(caches_dict, cache_attr_collector))

    off_chip_mems_dict = getComponentsOfTypesDict(system_info, off_chip_mem_ctrl_types)
    off_chip_mem_attr_collector = PreciseAttributeCollector(
        {
            "class": ["type"],
            "cache_type": ["type"],
            "response_latency": ["tCL"],
            "size": ["device_size"],
            "burst_length": ["burst_length"],
            "port": ["port", "peer", -2],
            # "rowbuffer_size": ["device_rowbuffer_size"], Not using for now as not in cacti
            "bus_width": ["device_bus_width"]
        },
        memory_units_inherit_attrs
    )
    print("Adding off chip components")
    off_chip_compound_components.extend(multipleComponentYamlData(off_chip_mems_dict, off_chip_mem_attr_collector, class_remap=off_chip_mem_ctrl_to_mem_type, other_attr_remap=off_chip_mem_ctrl_other_attr_remap))


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
    fu_to_op_mapping = getFunctionalUnitsToOpsMapping(cpu_info, fu_path, fu_num_prefix)
    print(fu_to_op_mapping)

    num_alu_units = 2
    num_mul_units = 1
    num_fpu_units = 1
    # these don't necessarily need to match up with length of the following lists
    # ex: funcUnit2 might do mul and funcUnit3 might div, so together they make
    #     one MUL unit
    ALU_units = [0, 1]
    MUL_units = [2, 3]
    FPU_units = [4]

    ALU_ops = mergeDictListValues(fu_to_op_mapping, ALU_units)
    MUL_ops = mergeDictListValues(fu_to_op_mapping, MUL_units)
    FPU_ops = mergeDictListValues(fu_to_op_mapping, FPU_units)

    # Now adding the execution unit, it is likely that special code will be required here
    # to not only create the execution unit but link relevant sub components
    exec_attr_collector = PreciseAttributeCollector(
        {
            "instruction_buffer_size": ["executeInputBufferSize"],
            "issue_width": ["executeIssueLimit"],
            "commit_width": ["executeCommitLimit"],
            "store_buffer_size": ["executeLSQMaxStoreBufferStoresPerCycle"],
            "prediction_width": ["branchPred", "numThreads"] # this stat is for branch predicition, might move later
                                                             # might need to make this it's own component
        }
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

    # read in the CPU statistics in the output file
    # stats_output_file_name = "m5out/stats.txt" # this is a default named directory/file location by gem5
    # stats_output_file = open(stats_output_file_name, "r")

    # cpu_general_stat_line_prefix = "system.cpu."
    # cpu_op_line_prefix = "system.cpu.op_class::"
    # cpu_general_stats = {}
    # cpu_op_stats = {}
    # memory_accesses_output_name_to_name = {
    #                                         "system.mem_ctrl.num_reads::.cpu.inst": "if_reads",
    #                                         "system.mem_ctrl.num_reads::.cpu.data": "mem_reads",
    #                                         "system.mem_ctrl.num_writes::.cpu.data": "mem_writes"
    #                                        }
    # memory_access_stats = {}
    # for line in stats_output_file:
    #     split_line = line.split()
    #     # skip entries that don"t have a name value pairing
    #     if len(split_line) < 2:
    #         continue
    #     full_stat_name = split_line[0]
    #     data_value = split_line[1]
    #     # skip data values of 0
    #     if data_value == "0":
    #         continue
    #     if full_stat_name.startswith(cpu_op_line_prefix):
    #         op = full_stat_name[len(cpu_op_line_prefix):]
    #         cpu_op_stats[op] = int(float(data_value))
    #     elif full_stat_name.startswith(cpu_general_stat_line_prefix):
    #         stat = full_stat_name[len(cpu_general_stat_line_prefix):]
    #         cpu_general_stats[stat] = int(float(data_value))
    #     elif full_stat_name in memory_accesses_output_name_to_name:
    #         mem_access_stat_name = memory_accesses_output_name_to_name[full_stat_name]
    #         memory_access_stats[mem_access_stat_name] = int(float(data_value))

    # printStats(cpu_general_stats, memory_access_stats, cpu_op_stats)


    
    # address_access_argument = {"data_delta": 1, "address_delta": 1}
    # action_count_yaml = {
    #     "action_counts": {
    #         "version": 0.3,
    #         "local": [
    #             {
    #                 "name": accelergy_architecture_name + ".if_unit",
    #                 "action_counts": [
    #                     {
    #                         "counts": memory_access_stats["if_reads"],
    #                         "name": "read",
    #                         "arguments": {"data_delta": 0, "address_delta": 1}
    #                     }
    #                 ]
    #             },
    #             {
    #                 "name": accelergy_architecture_name + ".rf_unit",
    #                 "action_counts": [
    #                     {
    #                         "counts": cpu_general_stats["num_int_register_reads"],
    #                         "name": "read",
    #                         "arguments": {"data_delta": 0, "address_delta": 1}
    #                     },
    #                     {
    #                         "counts": cpu_general_stats["num_int_register_writes"],
    #                         "name": "write",
    #                         "arguments": {"data_delta": 0, "address_delta": 1}
    #                     }
    #                 ]
    #             },
    #             {
    #                 "name": accelergy_architecture_name + ".alu_unit",
    #                 "action_counts": [
    #                     {
    #                         "counts": cpu_op_stats["IntAlu"],
    #                         "name": "intadd"
    #                     },
    #                     {
    #                         "counts": cpu_op_stats["IntMult"],
    #                         "name": "intmultiply"
    #                     },
    #                     {
    #                         "counts": cpu_op_stats["FloatAdd"],
    #                         "name": "fpadd"
    #                     },
    #                     {
    #                         "counts": cpu_op_stats["SimdFloatMult"],
    #                         "name": "fpmultiply"
    #                     }
    #                 ]
    #             },
    #             {
    #                 "name": accelergy_architecture_name + ".mm_unit",
    #                 "action_counts": [
    #                     {
    #                         "counts": cpu_op_stats["MemRead"],
    #                         "name": "load",
    #                         "arguments": {"data_delta": 0, "address_delta": 1}
    #                     },
    #                     {
    #                         "counts": cpu_op_stats["MemWrite"],
    #                         "name": "store",
    #                         "arguments": {"data_delta": 0, "address_delta": 1}
    #                     }
    #                 ]
    #             },
    #         ] 
    #     }
    # }
    # print(action_count_yaml)
    # action_counts_file = accelergy_input_dir + "/" + accelergy_action_counts_file_name
    # with open(action_counts_file, "w") as file:
    #     # dict_file = {"action_counts": {"version": 0.3, "local": [{"action_counts": [{"counts": 200, "name": "read", "arguments": {"data_delta": 0, "address_delta": 1}}], "name": "beta_pipeline.if_unit"}, {"action_counts": [{"counts": 200, "name": "read", "arguments": {"data_delta": 0, "address_delta": 1}}, {"counts": 100, "name": "write", "arguments": {"data_delta": 1, "address_delta": 1}}], "name": "beta_pipeline.rf_unit"}, {"action_counts": [{"counts": 100, "name": "intadd"}, {"counts": 100, "name": "intmac_op"}], "name": "beta_pipeline.alu_unit"}, {"action_counts": [{"counts": 100, "name": "load", "arguments": {"data_delta": 0, "address_delta": 1}}, {"counts": 100, "name": "store", "arguments": {"data_delta": 1, "address_delta": 1}}], "name": "beta_pipeline.mm_unit"}]}}
    #     documents = yaml.dump(action_count_yaml, file)

    # os.chdir("/home/ubuntu/five_stage_pipeline_components/five_stage_pipeline/input")
    # os.system("accelergy -o ../output/ *.yaml components/*.yaml -v 1")










