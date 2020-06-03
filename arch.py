class Arch:
    def __init__(self, connector_config, source_config):
        self.arch = {"name": "system"}  # architecture tree
        self.connector_config = connector_config
        self.source_config = source_config
        self.archMap = {}  # component map from arch to source
        self.classMap = connector_config["class_map"]  # class map from accelergy to gem5
        self.classInstances = {}  # instances of each gem5 class in source

        def buildClassInstances(source, path):
            if "type" in source:
                if source["type"] not in self.classInstances:
                    self.classInstances[source["type"]] = []
                self.classInstances[source["type"]].append(path)
            for key, value in source.items():
                if type(value) == dict:
                    buildClassInstances(value, path + "." + key)
        buildClassInstances(source_config["system"], "system")

    def addSubtree(self, path, name):
        component = self.getComponent(path)
        if "subtree" not in component:
            component["subtree"] = []
        component["subtree"].append({"name": name})

    def addLocal(self, path, name, accelergyType):
        component = self.getComponent(path)
        if "local" not in component:
            component["local"] = []
        component["local"].append({"name": name, "class": accelergyType})

    def addSystemAttr(self, name):
        self.addAttr("system", name, self.connector_config["system_attributes"][name])

    def addSourceAttr(self, path, name, sourcePath, field):
        self.addAttr(path, name, self.getSourceField(sourcePath + "." + field))

    def addAttr(self, path, name, value):
        component = self.getComponent(path)
        if "attributes" not in component:
            component["attributes"] = {}
        component["attributes"][name] = value

    def getComponent(self, path):
        def getSubcomponent(subcomponents, name):
            for subcomponent in subcomponents:
                if subcomponent["name"] == name:
                    return subcomponent
            return None
        names = path.split(".")
        if names[0] == self.arch["name"]:
            component = self.arch
        else:
            raise Exception("Unable to find component " + path)
        for name in names[1:]:
            nextComponent = None
            if "local" in component:
                nextComponent = getSubcomponent(component["local"], name)
            if nextComponent is None and "subtree" in component:
                nextComponent = getSubcomponent(component["subtree"], name)
            if nextComponent is None:
                raise Exception("Unable to find component " + path)
            component = nextComponent
        return component

    def getSource(self, path):
        names = path.split(".")
        source = self.source_config
        for name in names:
            if name in source:
                source = source[name]
            else:
                raise Exception("Unable to find source component" + path)
        return source

    def getSourceField(self, field):
        names = field.split(".")
        source = self.source_config
        for name in names:
            if name in source:
                source = source[name]
            else:
                raise Exception("Unable to find source field " + field)
        # unwrap lists of length 1
        if type(source) == list and len(source) == 1:
            return source[0]
        else:
            return source
