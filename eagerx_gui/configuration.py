from copy import deepcopy

# Terminal types
TERMS = {
    "object": {"in": {"actuators"}, "out": {"sensors", "states"}},
    "node": {"in": {"inputs"}, "out": {"outputs", "states"}},
    "reset_node": {
        "in": {"feedthroughs", "inputs", "targets"},
        "out": {"outputs", "states"},
    },
}
TERMS_IN = set().union(*[TERMS[key]["in"] for key in TERMS])
TERMS_OUT = set().union(*[TERMS[key]["out"] for key in TERMS])

# Possible entries in GUI
GUI_WIDGETS = {
    "node": {
        "hide": {
            "all": [],
            "actions": ["rate"],
            "observations": ["rate"],
        },
        "items": {
            "color": [
                "black",
                "red",
                "green",
                "yellow",
                "blue",
                "magenta",
                "cyan",
                "white",
                "grey",
            ],
            "log_level": {
                "silent": 0,
                "debug": 10,
                "info": 20,
                "warn": 30,
                "error": 40,
                "fatal": 50,
            },
            "log_level_memory": {
                "silent": 0,
                "debug": 10,
                "info": 20,
                "warn": 30,
                "error": 40,
                "fatal": 50,
            },
            "process": {"new process": 0, "environment": 1, "engine": 2, "external": 3},
        },
        "constant": {
            "all": list(set.union(TERMS_IN, TERMS_OUT, {"name", "entity_id", "launch_file"})),
            "actions": ["process"],
            "observations": ["process"],
        },
    },
    "term": {
        "items": {
            "repeat": ["all", "empty", "window"],
        },
        "constant": {
            "all": ["msg_type"],
            "feedthroughs": ["space_converter"],
        },
        "hide": {
            "all": ["address", "external_rate"],
            "states": ["converter"],
            "targets": ["space_converter"],
            "sensors": ["start_with_msg"],
            "actions": ["start_with_msg", "space_converter"],
            "observations": ["sync", "rate", "space_converter"],
            "outputs": ["rate"],
            "inputs": ["rate"],
        },
    },
}

ENGINE_GUI_WIDGETS = deepcopy(GUI_WIDGETS)
ENGINE_GUI_WIDGETS["term"]["hide"]["all"].remove("external_rate")
ENGINE_GUI_WIDGETS["term"]["hide"]["sensors"].append("external_rate")

# Corresponding RGB values for colors
GUI_COLORS = {
    "black": [0, 0, 0],
    "red": [255, 0, 0],
    "green": [0, 128, 0],
    "yellow": [255, 255, 0],
    "blue": [0, 0, 255],
    "magenta": [255, 0, 255],
    "cyan": [0, 255, 255],
    "white": [255, 255, 255],
}

# Config files to ignore in GUI
GUI_ENTITIES_TO_IGNORE = {
    "BaseConverter",
    "SpaceConverter",
    "Converter",
    "Processor",
    "EngineNode",
    "Engine",
    "EngineState",
}
GUI_NODE_IDS_TO_IGNORE = {
    "Observations",
    "Actions",
    "Render",
    "Supervisor",
    "Environment",
}
