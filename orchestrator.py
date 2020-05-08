''' 
IMPORTANT
This file must be run as python3 otherwise encoding issues will arise in the output files
'''
import os
import sys
import yaml
import json

from precise_attribute_collector import PreciseAttributeCollector

def getComponentsOfTypesDict(info_dict, types):
    '''
    Given a nested dictionary of information, return
    all dictionaries that have "type" attribute in types

    Parameters:
    info_dict (dict): A dict (potentially nested with other dict)
    types: A list of types

    Returns:
    dict: A dictionary mapping of all keys to dictionaries within info_dict
          that contain a "type" attribute that is within types input.
    '''
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
                              class_remap={}, other_attr_remap={}, add_name_as_attr=""):
    '''
    Get the YAML format for a list of components

    Parameters:
    components_dict (dict): A dictionary of component names to a dictionary with their respective
                            attributes
    attr_collector (PreciseAttributeCollector): An attribute collector used to collect the relevant
                                                attributes for each component from the components dict
    component_class (String): optional parameter to set the class of a component, if not
                              specified the class will be the component name by default unless
                              a "class" attribute is found
    class_remap (dict): optional mapping of class names to another class name they should actually take
    other_attr_remap (dict): optional mapping of attribute names to another name that should be
                             used instead if the attribute is found
    add_name_as_attr (string): optional attribute name that the name of the component should be
                               added as

    Returns:
    list: A list of yaml style components representing the components with their respective
          attributes
    '''
    yaml_components = []
    for component_name, component_dict in components_dict.items():
        print("Component name is: " + component_name)
        yaml_component = singleComponentYamlData(component_dict, attr_collector, component_name,
                                                 component_class=component_class, class_remap=class_remap,
                                                 other_attr_remap=other_attr_remap, add_name_as_attr=add_name_as_attr)
        yaml_components.append(yaml_component)
    return yaml_components

def singleComponentYamlData(component_info, attr_collector, component_name,
                            component_class="", class_remap={}, other_attr_remap={},
                            additional_attributes={}, add_name_as_attr=""):
    '''
    Get the YAML format for a single component

    Parameters:
    component_info (dict): Dictionary mapping a components attributes to its values
    component_name (string): The name of the component
    additional_attributes (dict): optional parameter specifying additional attributes
                                  that should be added
    The rest of the parameters are as in multipleComponentYamlData

    Returns:
    dict: A yaml style dict representing the component with its respective
          attributes
    '''
    if component_class == "":
        component_class = component_name
    attributes = {}
    attributes.update(additional_attributes)
    collected_attributes = attr_collector.get_attr_dict(component_info)
    attributes.update(collected_attributes)
    # handle remapping the 
    if "class" in attributes:
        component_class = attributes.pop('class', 'Class Not Found')
        if component_class in class_remap:
            component_class = class_remap[component_class]
        component_class = component_class.lower()
    if add_name_as_attr != "":
        print("For " + str(component_name) + " adding as attribute: " + str(add_name_as_attr))
        attributes[add_name_as_attr] = component_name.lower()
    for attr in attributes:
        if attr in other_attr_remap:
            value = attributes[attr]
            attr_remap_dict = other_attr_remap[attr]
            if value in attr_remap_dict:
                attributes[attr] = attr_remap_dict[value] 

    full_yaml_component = {"name": component_name, "class": component_class, "attributes": attributes}
    return full_yaml_component


def getActionCountsYAMLsForComponentsFromStats(components_to_full_component_path_name, attributes_to_stat_names, stat_lines):
    '''
    Parameters:
    components_to_full_component_path_name (dict): Mapping of components names to their full path
                                                   name in gem5
    attributes_to_stat_names (dict): Mapping of action names to the substring that will be present
                                     along with the full component path name in the stat line
                                     corresponding to this action name
    stat_lines (list): List of m5out stat lines split by whitespace

    Returns:
    dict: Yaml format of the action counts of each component, which is the name of 
          the component mapped to a list of dictionaries of with keys for the action name
          and action count mapped to their respective values
    '''
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

    return action_count_yamls

def createYAMLActionCountComponent(name, action_name_to_count):
    '''
    Parameters:
    name (str): The component name
    action_name_to_count: A dictionary of action names to their action count

    Returns:
    dict: Yaml format action counts for this component, which is a mapping of a "name" key
          to the component name, and a list of dictionaries for the actions each with a "name"
          key for the action name and a "counts" key for the number of action occurences
    '''
    yaml_component = {}
    yaml_component["name"] = name
    action_counts = []
    for action, count in action_name_to_count.items():
        new_action_count = {}
        new_action_count["name"] = action
        new_action_count["counts"] = count
        action_counts.append(new_action_count)
    yaml_component["action_counts"] = action_counts
    return yaml_component

def substringsPresentInSetKeys(substrings, string_set):
    '''
    Parameters:
    substring (List of string): The strings that we are checking if they are
                                present in any of the set's keys
    string_set (set): The set that we are searching through

    Returns:
    bool: True if any of the keys in string_set contain a substring in substrings, False otherwise
    '''
    for key in string_set:
        for substring in substrings:
            if substring in key:
                return True
    return False

def getFunctionalUnitsToOpSetMapping(cpu_info, fu_path, counts_included=False):
    '''
    Parameters:
    cpu_info (dict): Mapping of cpu attributes to their values (which may be contain additional 
                     sub values if they are a dictionary or list)
    fu_path (list of str): Of attributes to follow within the cpu to find the list of functional
                           units. All functional units have a "name" attribute that is prefixed
                           by the last string in the fu_path followed by the functional unit number

    Returns:
    dict: A dictionary where the keys are ALU_units, MUL_units, and FPU_units and each key
          maps to a dictionary of the functional unit number mapped to the operations that
          functional unit has
    '''
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
    fu_num_prefix = fu_path[-1]
    for fu in fu_units:
        fu_name = fu["name"]
        # some fu specify how many of the fu there are, as in O3 cpu, they do this with a count
        # attribute
        count = 1
        if "count" in fu:
            count = fu["count"]
        if fu_num_prefix not in fu_name:
            print("Error with getting fu num, prefix of: " + fu_num_prefix + " not present in name: " + fu_name)
        fu_num = fu_name[len(fu_num_prefix):]
        ops = recursivelyFindAttributeValues(fu, ["opClass"])
        op_set = set(ops)
        if count == 1:
            fu_to_op_mapping[fu_num] = op_set
        else:
            for i in range(0, count):
                fu_sub_num = fu_num + "-" + str(i)
                fu_to_op_mapping[fu_sub_num] = op_set

    # If these keywords are present in any op names for an FU we assume the FU type to be
    # the type for the keyword, if none is found we assume ALU by default
    FPU_keywords = ["Float"]
    MUL_keywords = ["Div", "Mul"]
    fu_mappings = {"ALU_units": {}, "MUL_units": {}, "FPU_units": {}}
    for fu, ops in fu_to_op_mapping.items():
        if substringsPresentInSetKeys(FPU_keywords, ops):
            fu_mappings["FPU_units"][fu] = ops
        elif substringsPresentInSetKeys(MUL_keywords, ops):
            fu_mappings["MUL_units"][fu] = ops
        else:
            fu_mappings["ALU_units"][fu] = ops
    return fu_mappings

def mergeDictSetValuesForKeys(key_to_set):
    '''
    Parameters:
    key_to_set_dict (dict): A dictionary mapping string keys to sets of values

    Returns:
    set: A set containing all of the merged values
    '''
    merged_values = set()
    for key in key_to_set:
        merged_values = merged_values.union(key_to_set[key])
    return merged_values

def recursivelyFindAttributeValues(info, attributes_to_find):
    '''
    Parameters:
    info (dict or list): A dictionary or list containing attributes, potentially mapping/indexing
                         to other dict or list
    attributes_to_find (list): A list of attributes to find, searching recursively in info

    Returns:
    list: A list of all values mapped to by attributes_to_find within info
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
    '''
    Parameters:
    ops (list): List of op names to search for in stat_lines to get the associated action count
    stat_lines: List of m5out stat lines split by whitespace

    Returns:
    dict: Mapping of each operation in ops to the number of times the op occurred as
          reported by the gem5 stats
    '''
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

    # Run the command to run our architecture on our designated workload
    

    # To specify via CLI, maybe -g, -i, -o, -m flags?
    # -g gem5 directory path
    # -i directory path to put accelergy input
    # -o directory path to put accelergy output
    # -c config file path for this converter
    m5out_directory_path = "m5out"
    accelergy_input_dir = "example_input"
    accelergy_output_dir = "example_output"
    config_file_path = "example_connector_config_file.yaml"
    # this is the path to our list of functional units within our CPU
    fu_path = ["executeFuncUnits", "funcUnits"]

    # first copy over the components required by our converted architecture to the
    # destination input directory
    base_input_dir_path = "./input"
    os.system("cp -r " + base_input_dir_path + " " + accelergy_input_dir)

    gem5_config_file_path = m5out_directory_path + "/config.json"
    # read in accelergy configuration
    with open(gem5_config_file_path) as f:
        config_data = json.load(f)
    system_info = config_data["system"]
    cpu_info = system_info["cpu"]

    system_attributes = {"technology": "45nm", "datawidth": 32}
    cpu_attributes = {}
    on_chip_compound_components = []
    off_chip_compound_components = []

    cache_types = ["Cache"]
    off_chip_mem_ctrl_types = ["DRAMCtrl"]
    off_chip_mem_ctrl_to_mem_type = {"dramctrl": "memory_controller"} # as per McPat
    off_chip_mem_ctrl_other_attr_remap = {
        "memory_type": {
            "dramctrl": "main_memory"
        }
    }
    mem_bus_types = ["CoherentXBar"]
    tlb_types = ["RiscvTLB"] # need to add other ISAs later

    # collect the system level attributes we care about
    system_attr_collector = PreciseAttributeCollector(
        {
            "clockrate": ["clk_domain", "clock"], # in MHz (Megahertz)
            "block_size": ["cache_line_size"],
            "vdd": ["clk_domain", "voltage_domain", "voltage"]
        }
    )
    system_attributes.update(system_attr_collector.get_attr_dict(system_info))
    # collect the cpu level attributes we care about
    # attributes that cpu inherits from the system if not specified for the cpu
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

    # attributes that memory inherits from the system if not specified for the unit
    memory_units_inherit_system_attrs = ["technology", "block_size", "clockrate"]
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

    # I am tentatively treating all cache Components as on-chip, as it appears
    # that as of right now only the icache and dcache can be specified within the cpu,
    # thus the other caches are attributes of the entire system
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
    fu_mappings = getFunctionalUnitsToOpSetMapping(cpu_info, fu_path)

    # calculate the number of each type of functional unit for config
    num_alu_units = len(fu_mappings["ALU_units"])
    num_mul_units = len(fu_mappings["MUL_units"])
    num_fpu_units = len(fu_mappings["FPU_units"])

    # get the operations for each type of fu based on their ops present
    ALU_ops = mergeDictSetValuesForKeys(fu_mappings["ALU_units"])
    MUL_ops = mergeDictSetValuesForKeys(fu_mappings["MUL_units"])
    FPU_ops = mergeDictSetValuesForKeys(fu_mappings["FPU_units"])

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

    # arbitrary architecture name chosen
    accelergy_architecture_name = "system_arch"
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

    with open(accelergy_input_dir + "/architecture.yaml", "w") as file:
        yaml.dump(architecture_yaml, file, sort_keys=False)

    ######################## Now to get action counts #############################
    gem5_stats_file_path = m5out_directory_path + "/stats.txt"
    # read in accelergy stats
    stat_lines = []
    with open(gem5_stats_file_path) as f:
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
        off_chip_mem_name_to_full_path_name[mem_name] = accelergy_architecture_name + "." + mem_name

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

    accelergy_action_counts_file_name = accelergy_input_dir +  "/action_counts.yaml"
    with open(accelergy_action_counts_file_name, "w") as file:
        yaml.dump(action_counts_yaml, file, sort_keys=False)

    accelergy_command = "accelergy -o " + accelergy_output_dir + " " + accelergy_input_dir + "/*.yaml "  + accelergy_input_dir + "/components/*.yaml -v 1"
    print("Accelergy command is: ")
    print(accelergy_command)
    os.system(accelergy_command)
