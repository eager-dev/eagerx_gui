from eagerx.utils.utils import get_attribute_from_module


def get_yaml_type(yaml):
    if "node_type" in yaml:
        if "targets" in yaml:
            type = "reset_node"
        else:
            type = "node"
    else:
        type = "object"
    return type


def get_nodes_and_objects_library():
    from eagerx.core.register import REGISTRY

    library = dict()
    for entity_cls, entities in REGISTRY.items():
        library[entity_cls.__name__] = []
        for id, entry in entities.items():
            spec = entry["spec"]
            cls = get_attribute_from_module(entry["cls"])
            library[entity_cls.__name__].append({"entity_id": id, "spec": spec, "entity_cls": entity_cls, "cls": cls})
    return library
