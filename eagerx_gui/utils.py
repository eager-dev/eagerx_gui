import numpy as np
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


def get_connected_nodes(state, node):
    # Get a set of all the nodes that are connected directly to some node
    connected_inputs = set()
    connected_outputs = set()
    for source, target in state["connects"]:
        if source[0] == node:
            connected_outputs.add(target[0])
        elif target[0] == node:
            connected_inputs.add(source[0])
    return connected_inputs, connected_outputs


def is_connected_to_fixed(state, node, fixed_nodes, nodes_to_ignore=None):
    # Check if node is connected to any fixed node (direct or indirect)
    if nodes_to_ignore is None:
        nodes_to_ignore = set()
    nodes_to_ignore.add(node)
    connected_inputs, connected_outputs = get_connected_nodes(state, node)
    connected_nodes = set.union(connected_inputs, connected_outputs)
    for connected_node in connected_nodes:
        if connected_node in nodes_to_ignore:
            continue
        elif connected_node in fixed_nodes:
            return True
        elif is_connected_to_fixed(state, connected_node, fixed_nodes, nodes_to_ignore):
            return True
    return False


def get_longest_shortest_simple_paths(state, fixed_nodes=None):
    """
    Calculates shortest simple path for each fixed node as source and other node as target.
    Returns the longest for each fixed node.
    """
    if fixed_nodes is None:
        fixed_nodes = {}

    G = nx.DiGraph()
    longest_shortest_simple_paths = {}
    for node in state["nodes"].keys():
        G.add_node(node)
    for source, target in state["connects"]:
        source_name, _, _ = source
        target_name, _, _ = target
        G.add_edge(source_name, target_name)
    for source in fixed_nodes:
        longest_shortest_simple_path = []
        if source not in state["nodes"].keys():
            continue
        for target in state["nodes"].keys():
            if source == target or ("env/observations" in [source, target] and "env/render" in [source, target]):
                continue
            if nx.has_path(G, source=source, target=target):
                simple_paths = nx.all_simple_paths(G, source=source, target=target)
                # Initialize shortest path length with max (i.e. number of nodes) such that each existing path would be shorter
                shortest_path_len = len(state["nodes"].keys())
                shortest_path = []
                for simple_path in simple_paths:
                    if len(simple_path) < shortest_path_len:
                        shortest_path = simple_path
                        shortest_path_len = len(shortest_path)
                if shortest_path_len > len(longest_shortest_simple_path):
                    longest_shortest_simple_path = shortest_path
        longest_shortest_simple_paths[source] = longest_shortest_simple_path
    return longest_shortest_simple_paths


def add_pos_to_state(state, is_engine=False):
    """
    Position nodes using Fruchterman-Reingold force-directed algorithm.
    """
    # Initialize fixed nodes
    left_nodes = {"actuators"} if is_engine else {"env/actions"}
    if is_engine:
        right_nodes = {"sensors"}
    elif "env/render" in state["nodes"].keys():
        right_nodes = {"env/observations", "env/render"}
    else:
        right_nodes = {"env/observations"}

    fixed_nodes = set.union(left_nodes, right_nodes)
    node_size = 150

    # Check for which nodes the position is prescribed
    G = nx.Graph()
    for node, params in state["nodes"].items():
        G.add_node(node)
        if node not in state["gui_state"]:
            state["gui_state"][node] = empty_gui_state()  # Add gui states here.
        gui_state = state["gui_state"][node]
        if gui_state.get("pos", None) is not None and len(gui_state["pos"]) == 2:
            fixed_nodes.add(node)
    for source, target in state["connects"]:
        source_name, _, _ = source
        target_name, _, _ = target
        G.add_edge(source_name, target_name)

    fixed_clusters = []
    loose_clusters = []
    fixed_cluster_nodes = set()
    clusters = nx.connected_components(G)
    for cluster in clusters:
        fixed = False
        for fixed_node in fixed_nodes:
            if fixed_node in cluster:
                fixed_clusters.append(cluster)
                fixed_cluster_nodes.update(cluster)
                fixed = True
                break
        if not fixed:
            loose_clusters.append(cluster)

    # Create Graph
    G = nx.Graph()
    for node in fixed_cluster_nodes:
        G.add_node(node)
    for source, target in state["connects"]:
        source_name, _, _ = source
        target_name, _, _ = target
        if source_name in fixed_cluster_nodes:
            G.add_edge(source_name, target_name)

    # Get longest path in order to set x locations
    longest_shortest_simple_paths = get_longest_shortest_simple_paths(state, fixed_nodes=set.union(left_nodes, right_nodes))

    x_max = 0
    left_max = 0
    right_max = 0
    for left_node in left_nodes:
        len_left = node_size * len(longest_shortest_simple_paths[left_node])
        if len_left > left_max:
            left_max = len_left
        for right_node in right_nodes:
            len_right = node_size * len(longest_shortest_simple_paths[right_node])
            if len_right > right_max:
                right_max = len_right
            if nx.has_path(G, left_node, right_node):
                longest_left = len(longest_shortest_simple_paths[left_node])
                longest_right = len(longest_shortest_simple_paths[right_node])
                max_path_len = node_size * max(longest_left, longest_right)
                if right_node not in longest_shortest_simple_paths[left_node]:
                    max_path_len += node_size
                if max_path_len > x_max:
                    x_max = max_path_len
    if x_max == 0:
        x_max = left_max + right_max + 2 * node_size

    left_connected_clusters = {}
    connected_clusters = {}
    y_pos = {}
    for fixed_node in fixed_nodes:
        connected_inputs, connected_outputs = get_connected_nodes(state, fixed_node)
        if fixed_node in left_nodes:
            left_connected_clusters[fixed_node] = {}
            left_connected_clusters[fixed_node]["in"] = connected_inputs
            left_connected_clusters[fixed_node]["out"] = connected_outputs
        else:
            connected_clusters[fixed_node] = {}
            connected_clusters[fixed_node]["in"] = connected_inputs
            connected_clusters[fixed_node]["out"] = connected_outputs
    for key, connected_cluster in {**left_connected_clusters, **connected_clusters}.items():
        y_pos[key] = {}
        y_pos[key]["in"] = -((len(connected_cluster["in"]) - 1) / 2) * node_size
        y_pos[key]["out"] = -((len(connected_cluster["out"]) - 1) / 2) * node_size

    fixed_positions = dict()
    for fixed_cluster in fixed_clusters:
        for node in sorted(fixed_cluster):
            params = state["nodes"][node]
            gui_state = state["gui_state"][node]
            if params["config"]["name"] in fixed_nodes:
                if gui_state.get("pos", None) is not None and len(gui_state["pos"]) == 2:
                    pos = gui_state["pos"]
                elif params["config"]["name"] in left_nodes:
                    pos = [0, 0]
                elif params["config"]["name"] == "env/render":
                    pos = [x_max, node_size - y_pos["env/observations"]["in"] - y_pos["env/render"]["in"]]
                else:
                    pos = [x_max, 0]
                fixed_positions[node] = pos
    for fixed_cluster in fixed_clusters:
        for node in sorted(fixed_cluster):
            params = state["nodes"][node]
            if not params["config"]["name"] in fixed_nodes:
                for key, clusters in left_connected_clusters.items():
                    for direction in {"in", "out"}:
                        if node in clusters[direction] and node not in fixed_positions.keys():
                            x_pos_cluster = fixed_positions[key][0]
                            if direction == "in":
                                x_pos_cluster -= 1.25 * node_size
                            else:
                                x_pos_cluster += 1.25 * node_size
                            fixed_positions[node] = [x_pos_cluster, fixed_positions[key][1] + y_pos[key][direction]]
                            y_pos[key][direction] += node_size
                            break
                for key, clusters in connected_clusters.items():
                    for direction in {"in", "out"}:
                        if node in clusters[direction] and node not in fixed_positions.keys():
                            x_pos_cluster = fixed_positions[key][0]
                            if direction == "in":
                                x_pos_cluster -= 1.25 * node_size
                            else:
                                x_pos_cluster += 1.25 * node_size
                            fixed_positions[node] = [x_pos_cluster, fixed_positions[key][1] + y_pos[key][direction]]
                            y_pos[key][direction] += node_size
                            break

    position_dict = nx.spring_layout(G, k=1.5 * 150, pos=fixed_positions, fixed=fixed_positions.keys())
    for node, pos in position_dict.items():
        state["gui_state"][node]["pos"] = pos.tolist()
    y_offset = np.max(np.array(list(position_dict.values()))[:, 1]) + node_size
    x_offset = x_max // 2
    for loose_cluster in loose_clusters:
        G = nx.Graph()
        for node in sorted(loose_cluster):
            G.add_node(node)
        for source, target in state["connects"]:
            source_name, _, _ = source
            target_name, _, _ = target
            if source_name in loose_cluster:
                G.add_edge(source_name, target_name)
        position_dict = nx.spring_layout(G, k=1)
        height = (
            abs(
                np.max(np.array(list(position_dict.values()))[:, 1]) + np.min(np.array(list(position_dict.values()))[:, 1]) + 2
            )
            * node_size
        )
        y_offset += height // 2
        if np.min(np.array(list(position_dict.values()))[:, 1]) * node_size < 0:
            y_offset += abs(np.min(np.array(list(position_dict.values()))[:, 1]) * node_size)
        for node, pos in position_dict.items():
            pos *= node_size
            pos += np.array([x_offset, y_offset])
            state["gui_state"][node]["pos"] = pos.tolist()
        y_offset += height // 2
    return state
