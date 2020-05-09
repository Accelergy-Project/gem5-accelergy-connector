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
