from util_helper import *

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
