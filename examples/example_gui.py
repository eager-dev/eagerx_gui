import eagerx
import eagerx.engines.openai_gym as eagerx_gym
from matplotlib import pyplot as plt


if __name__ == "__main__":
    # Define rate (depends on rate of gym env)
    rate = 20

    # Define object
    from eagerx.engines.openai_gym.objects import GymObject
    gym_id = "Pendulum-v1"  # 'Pendulum-v0', 'Acrobot-v1', 'CartPole-v1', 'MountainCarContinuous-v0'
    name = gym_id.split("-")[0]
    obj = GymObject.make(name, env_id=gym_id, rate=rate, default_action=[0.], render_shape=[300, 300])
    obj2 = GymObject.make("obj2", env_id=gym_id, rate=rate, default_action=[0.], render_shape=[300, 300])

    # Define graph
    graph = eagerx.Graph.create(objects=[obj])
    graph.connect(source=obj.sensors.observation,   observation="observation",      window=1)
    graph.connect(source=obj.sensors.reward,        observation="reward",           window=1)
    graph.connect(source=obj.sensors.terminated,    observation="terminated",       window=1)
    graph.connect(source=obj.sensors.truncated,     observation="truncated",        window=1)
    graph.connect(action="action",                  target=obj.actuators.action,    window=1)

    # Add rendering
    graph.add_component(obj.sensors.image)
    graph.render(source=obj.sensors.image, rate=10, encoding="rgb")

    # Open gui
    # graph.gui()

    # Open render of gui
    # gui_render = graph.gui(interactive=False, filename="graph.svg")

    # Show GUI render
    # plt.rcParams["figure.figsize"] = [10.00, 10.00]
    # plt.axis("off")
    # plt.imshow(gui_render)
    # plt.show()

    # Define engine
    from eagerx.engines.openai_gym.engine import GymEngine
    engine = GymEngine.make(rate=rate, sync=True, real_time_factor=0, process=eagerx.NEW_PROCESS)

    # obj.gui(GymEngine)
    # engine_gui_render = obj.gui(GymEngine, interactive=False, filename="engine_graph", resolution=[3000, 3000])

    # Show GUI render
    # plt.rcParams["figure.figsize"] = [10.00, 10.00]
    # plt.axis("off")
    # plt.imshow(engine_gui_render)
    # plt.show()

    # Define backend
    # from eagerx.backends.ros1 import Ros1
    # backend = Ros1.make()
    from eagerx.backends.single_process import SingleProcess
    SingleProcess.MIN_THREADS = 50
    backend = SingleProcess.make()

    # Initialize Environment
    env = eagerx_gym.EagerxGym(name="rx", rate=rate, graph=graph, engine=engine, backend=backend, render_mode="human")

    # Open GUI
    env.gui()

    # Start evaluation
    import time
    for j in range(50):
        print("\n[Episode %s]" % j)
        (_obs, _info), done = env.reset(), False
        env.render()
        start = time.time()
        N = 0
        while not done:
            N += 1
            action = env.action_space.sample()
            _obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
        print(f"FPS: {N / (time.time() - start)}")
    env.shutdown()

