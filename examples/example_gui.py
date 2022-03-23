# EAGERx imports
from eagerx import Object, Bridge, Node, ResetNode, Converter, BaseConverter
from eagerx import initialize, log, process

initialize("eagerx_core", anonymous=True, log_level=log.DEBUG)

# Environment imports
from eagerx.core.graph import Graph

# Implementation specific
import eagerx.bridges.test  # noqa # pylint: disable=unused-import

if __name__ == "__main__":
    # Process configuration (optional)
    node_p = process.NEW_PROCESS
    bridge_p = process.NEW_PROCESS
    rate = 7

    # Define nodes
    N1 = Node.make("Process", "N1", rate=1.0, process=node_p)
    KF = Node.make("KalmanFilter", "KF", rate=rate, process=node_p, inputs=["in_1", "in_2"], outputs=["out_1", "out_2"])
    N3 = ResetNode.make("RealReset", "N3", rate=rate, process=node_p, inputs=["in_1", "in_2"], targets=["target_1"])

    # Define object
    viper = Object.make("Viper", "obj", position=[1, 1, 1], actuators=["N8"], sensors=["N6"], states=["N9"])

    # Define converter (optional)
    RosString_RosUInt64 = Converter.make("RosString_RosUInt64", test_arg="test")
    RosImage_RosUInt64 = Converter.make("RosImage_RosUInt64", test_arg="test")

    # Define graph
    graph = Graph.create(nodes=[N3, KF], objects=[viper])
    graph.connect(source=viper.sensors.N6, observation="obs_1", delay=0.0)
    graph.connect(source=KF.outputs.out_1, observation="obs_3", delay=0.0)
    graph.connect(source=viper.sensors.N6, target=KF.inputs.in_1, delay=0.0)
    graph.connect(action="act_2", target=KF.inputs.in_2, skip=True)
    graph.connect(action="act_2", target=N3.feedthroughs.out_1, delay=0.0)
    graph.connect(source=viper.sensors.N6, target=N3.inputs.in_1)
    graph.connect(source=viper.states.N9, target=N3.targets.target_1)
    graph.connect(
        source=N3.outputs.out_1,
        target=viper.actuators.N8,
        delay=0.0,
        converter=RosString_RosUInt64,
    )

    # Replace output converter
    identity = BaseConverter.make("Identity")
    # Disconnects all connections (obs_1, KF, N3)
    graph.set({"converter": RosString_RosUInt64}, viper.sensors.N6)
    graph.set({"converter": identity}, viper.sensors.N6)
    # graph.render(source=viper.sensors.N6, rate=1, converter=RosImage_RosUInt64)  # Reconnect
    graph.connect(source=viper.sensors.N6, observation="obs_1", delay=0.0)  # Reconnect
    graph.connect(source=viper.sensors.N6, target=KF.inputs.in_1, delay=0.0)  # Reconnect
    graph.connect(source=viper.sensors.N6, target=N3.inputs.in_1)  # Reconnect

    # Remove component. For action/observation use graph._remove_action/observation(...) instead.
    graph.remove_component(N3.inputs.in_2)

    # Rename action & observation
    graph.rename("act_1", action="act_2")
    graph.rename("obs_2", observation="obs_3")

    # Remove & add action (without action terminal removal)
    graph.disconnect(action="act_1", target=KF.inputs.in_2)
    graph.connect(
        action="act_1",
        target=KF.inputs.in_2,
        converter=None,
        delay=None,
        window=None,
        skip=True,
    )

    # Remove & add observation (with observation terminal removal)
    graph.disconnect(source=viper.sensors.N6, observation="obs_1")
    graph.add_component(observation="obs_1")  # Add input terminal
    graph.connect(
        source=viper.sensors.N6,
        observation="obs_1",
        converter=None,
        delay=None,
        window=None,
    )

    # Remove & add other input
    graph.disconnect(source=viper.sensors.N6, target=KF.inputs.in_1)
    graph.connect(source=viper.sensors.N6, target=KF.inputs.in_1)

    # TEST Test with KF having skipped all inputs at t=0
    graph.remove_component(KF.inputs.in_1)

    graph.gui()

    # Test save & load functionality
    graph.save("./test.graph")
    graph.load("./test.graph")
