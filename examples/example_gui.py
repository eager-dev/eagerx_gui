# EAGERx imports
import eagerx
from eagerx.core.graph import Graph
from eagerx_gui import render_gui
import matplotlib.pyplot as plt

# Implementation specific
import eagerx.engines.openai_gym as eagerx_gym
import eagerx.nodes

if __name__ == "__main__":
    roscore = eagerx.initialize(
        "eagerx_core", anonymous=True, log_level=eagerx.log.INFO
    )

    # Define rate (depends on rate of gym env)
    rate = 20
    n_objects = 5

    # Define object
    id = "Acrobot-v1"  # 'Pendulum-v0', 'Acrobot-v1', 'CartPole-v1', 'MountainCarContinuous-v0'
    object_name = id.split("-")[0]

    graph = Graph.create()

    objects = []
    for i in range(n_objects):
        name = f"{object_name}_{i}"
        obj = eagerx.Object.make("GymObject", name, env_id=id, sensors=["observation", "reward", "done", "image"], rate=rate)
        graph.add(obj)
        if i == 0:
            graph.render(source=obj.sensors.image, rate=10)
            graph.connect(source=obj.sensors.observation, observation="observation", window=1)
            graph.connect(source=obj.sensors.reward, observation="reward", window=1)
            graph.connect(source=obj.sensors.done, observation="done", window=1)
            graph.connect(action="action", target=obj.actuators.action, window=1)

            name2 = f"{object_name}_{i}_{0}"
            obj2 = eagerx.Object.make("GymObject", name2, env_id=id, sensors=["observation", "reward", "done", "image"],
                                      rate=rate)
            graph.add(obj2)
            graph.connect(source=obj.sensors.observation, target=obj2.actuators.action)
            for j in range(n_objects):
                name3 = f"{object_name}_{i}_{1+2*j}"
                obj3 = eagerx.Object.make("GymObject", name3, env_id=id, sensors=["observation", "reward", "done", "image"],
                                          rate=rate)
                graph.add(obj3)

                if j == 0:
                    graph.connect(source=obj2.sensors.observation, target=obj3.actuators.action)
                else:
                    graph.connect(source=obj4.sensors.observation, target=obj3.actuators.action)
                name4 = f"{object_name}_{i}_{2+2*j}"
                obj4 = eagerx.Object.make("GymObject", name4, env_id=id, sensors=["observation", "reward", "done", "image"],
                                          rate=rate)
                graph.add(obj4)
                graph.connect(source=obj3.sensors.observation, target=obj4.actuators.action)

            graph.connect(source=obj4.sensors.observation, observation="observation_2")
        else:
            for j in range(i):
                name2 = f"{object_name}_{i}_{j}"
                obj2 = eagerx.Object.make("GymObject", name2, env_id=id, sensors=["observation", "reward", "done", "image"], rate=rate)
                graph.add(obj2)
                graph.connect(source=obj.sensors.observation, target=obj2.actuators.action)



    # Open gui
    obj.gui("GymEngine")
    graph.gui()
    rgb = render_gui(graph._state)
    plt.imshow(rgb)
    plt.show()
    
    # Define engine
    engine = eagerx.Engine.make(
        "GymEngine",
        rate=rate,
        sync=True,
        real_time_factor=1,
        process=eagerx.process.NEW_PROCESS,
    )
