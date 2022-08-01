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
    },
    "term": {
        "hide": {
            "all": ["address"],
            "states": ["processor"],
            "observations": ["sync", "rate"],
            "outputs": ["rate"],
            "inputs": ["rate"],
        },
    },
}

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
