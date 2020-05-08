class PreciseAttributeCollector:
    # An attribute collector looking for exact matches of attribute names present in 
    # a component dictionary which contains a componenets attributes mapped to their value
    def __init__(self, attr_to_path, inherit_attr={}):
        '''
        attr_to_path (dict): Dictionary with mapping of attribute names to what their
                             path in a dictionary would be
                             A number can be included at the end to indicate the index of 
                             a value in a string with . separating names
                             ie: "system.l2bus.slave[1]"
                                 if we want l2bus (or the equivelant on all such paths)
                                 the int value is -2

        inherit_attr (dict): Dictionary mapping attributes to a value that they should inherit
                             regardless of whether this attribute is in attr_to_path
        '''
        self.attr_to_path = attr_to_path
        self.inherit_attr = inherit_attr

    def get_attr_dict(self, info_dict):
        '''
        Parameters
        info_dict (dict): A dictionary mapping the attributes of a specific component to
                          their values, with potentially dict values with more attributes nested.

        Returns
        dict: A dictionary mapping all found attributes in attr_to_path specified by their
              path to their value, additionally including any attributes present in inherit_attr
        '''
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
        '''
        Parameters
        path: A list of keys by which to recursively search info_dict finally returning
              the value mapped to by the last key, unless there is an int at the end, in
              which case specifying the index of the value to return if it is split by "."
        info_dict (dict): A dictionary mapping the attributes of a specific component to
                          their values, with potentially dict values with more attributes nested.

        Returns:
        string or int: The value if it can be found, None if it is not found
        '''
        # base cases
        if len(path) == 1:
            if path[0] in info_dict:
                # this is to handle the case of returning the first element in a list
                if isinstance(info_dict[path[0]], list):
                    return info_dict[path[0]][0]
                return info_dict[path[0]]
            return None
        elif len(path) == 2 and isinstance(path[1], int):
            # this is used to get a subset of a path split by "." and indexed by an int.
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
