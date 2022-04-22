from eagerx.utils.utils import get_attribute_from_module
import networkx as nx
import ast


def tryeval(val):
    try:
        val = ast.literal_eval(val)
    except Exception as e:
        if isinstance(e, ValueError):
            pass
        elif isinstance(e, SyntaxError):
            pass
        else:
            raise
    return val


def empty_gui_state():
    return dict(pos=None, linestyle=dict())


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


def get_connected_nodes(state, node):
    # Get a set of all the nodes that are connected directly to some node
    connected_nodes = set()
    for source, target in state["connects"]:
        if source[0] == node:
            connected_nodes.add(target[0])
        elif target[0] == node:
            connected_nodes.add(source[0])
    return connected_nodes


def is_connected_to_fixed(state, node, fixed_positions, nodes_to_ignore=None):
    # Check if node is connected to any fixed node (direct or indirect)
    if nodes_to_ignore is None:
        nodes_to_ignore = set()
    nodes_to_ignore.add(node)
    connected_nodes = get_connected_nodes(state, node)
    for connected_node in connected_nodes:
        if connected_node in nodes_to_ignore:
            continue
        elif connected_node in fixed_positions.keys():
            return True
        elif is_connected_to_fixed(state, connected_node, fixed_positions, nodes_to_ignore):
            return True
    return False


def add_pos_to_state(state, fixed_nodes=["env/actions", "env/observations", "env/render"]):
    # Position nodes using Fruchterman-Reingold force-directed algorithm.
    node_size = 150
    G = nx.Graph()
    fixed_positions = {}
    disconnected_y = node_size
    x_pos = node_size * (2 + max((len(state["nodes"].items()) - 3) // 2, 2))

    for node, params in state["nodes"].items():
        if node not in state["gui_state"]:
            state["gui_state"][node] = empty_gui_state()  # Add gui states here.
        gui_state = state["gui_state"][node]
        if gui_state.get("pos", None) is not None and len(gui_state["pos"]) == 2:
            fixed_positions[node] = gui_state["pos"]
        elif params["config"]["name"] in fixed_nodes:
            if params["config"]["name"] == fixed_nodes[0]:
                pos = [0, 0]
            elif params["config"]["name"] == fixed_nodes[1]:
                pos = [x_pos, 0]
            else:
                pos = [x_pos, node_size]
            fixed_positions[node] = pos
        elif not is_connected_to_fixed(state, node, fixed_positions):
            fixed_positions[node] = [0, disconnected_y]
            disconnected_y += node_size
        G.add_node(node)
    for source, target in state["connects"]:
        source_name, _, _ = source
        target_name, _, _ = target
        G.add_edge(source_name, target_name)
    position_dict = nx.spring_layout(G, k=node_size, pos=fixed_positions, fixed=fixed_positions.keys())
    for node, pos in position_dict.items():
        state["gui_state"][node]["pos"] = pos.tolist()
    return state


def add_pos_to_engine_state(state, fixed_nodes=["actuators", "sensors"]):
    # Position nodes using Fruchterman-Reingold force-directed algorithm.
    node_size = 150
    G = nx.Graph()
    fixed_positions = {}
    x_pos = node_size * (2 + max((len(state["nodes"].items()) - 3) // 2, 3))

    # First get two clusters of nodes, i.e. actions and observations cluster
    clusters = {}
    y_pos = {}
    for fixed_node in fixed_nodes:
        clusters[fixed_node] = get_connected_nodes(state, fixed_node)

    for key, cluster in clusters.items():
        y_pos[key] = -((len(cluster) - 1) / 2) * node_size

    for node, params in state["nodes"].items():
        if node not in state["gui_state"]:
            state["gui_state"][node] = empty_gui_state()  # Add gui states here.
        gui_state = state["gui_state"][node]
        if gui_state.get("pos", None) is not None and len(gui_state["pos"]) == 2:
            fixed_positions[node] = gui_state["pos"]
        elif params["config"]["name"] in fixed_nodes:
            x_pos = node_size * (2 + max((len(state["nodes"].items()) - 3) // 2, 2))
            if params["config"]["name"] == fixed_nodes[0]:
                pos = [0, 0]
            else:
                pos = [x_pos, 0]
            fixed_positions[node] = pos
        else:
            for key, cluster in clusters.items():
                if node in cluster:
                    if key == fixed_nodes[0]:
                        x_pos_cluster = 1.25 * node_size
                    else:
                        x_pos_cluster = x_pos - 1.25 * node_size
                    fixed_positions[node] = [x_pos_cluster, y_pos[key]]
                    y_pos[key] += node_size
                    break
        G.add_node(node)
    for source, target in state["connects"]:
        source_name, _, _ = source
        target_name, _, _ = target
        G.add_edge(source_name, target_name)
    position_dict = nx.spring_layout(G, k=node_size, pos=fixed_positions, fixed=fixed_positions.keys())
    for node, pos in position_dict.items():
        state["gui_state"][node]["pos"] = pos.tolist()
    return state
