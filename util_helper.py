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

def checkIfPathExists(info, path):
    '''
    Parameters
    info (dict or list): A dictionary or list containing attributes, potentially mapping/indexing
                         to other dict or list
    path: A path to be followed via indexing in info

    Returns:
    True if the path following each attribute in path through info exists, false if it does not
    '''
    if len(path) == 0:
        return True
    else:
        if path[0] in info:
            return checkIfPathExists(info[path[0]], path[1:])
        else:
            return False
