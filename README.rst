******************
eagerx_gui package
******************

.. image:: https://img.shields.io/badge/License-Apache_2.0-blue.svg
   :target: https://opensource.org/licenses/Apache-2.0
   :alt: license

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black
   :alt: codestyle

.. image:: https://github.com/eager-dev/eagerx_gui/actions/workflows/ci.yml/badge.svg?branch=master
  :target: https://github.com/eager-dev/eagerx_gui/actions/workflows/ci.yml
  :alt: Continuous Integration

.. contents:: Table of Contents
    :depth: 2

What is the *eagerx_gui* package?
#################################

This repository/package provides GUI functionality for EAGERx.
It allows to view graphs created using EAGERx, but also allows to create graphs interactively using the GUI.
EAGERx (Engine Agnostic Gym Environments for Robotics) enables users to easily define new tasks, switch from one sensor to another, and switch from simulation to reality with a single line of code by being invariant to the physics engine.

`The core repository is available here <https://github.com/eager-dev/eagerx>`_.

`Full documentation and tutorials (including package creation and contributing) are available here <https://eagerx.readthedocs.io/en/master/>`_.

Installation
############

You can install the package using pip:

.. code:: shell

    pip3 install eagerx-gui

.. note::
    EAGERx depends on a minimal ROS installation. Fortunately, you **can** use eagerx anywhere as you would any python package,
    so it does **not** impose a ROS package structure on your project.

Example
#######

The GUI can be used for visualising a `graph <https://eagerx.readthedocs.io/en/master/guide/api_reference/graph/graph.html>`_ that is created within EAGERx.
Also, a complete graph can be created using the GUI as shown in the GIF below.

.. image:: figures/gui.GIF

The code used for this example is the following:

.. code:: python
    
    import eagerx
    from eagerx.wrappers import Flatten
    
    # Register components (objects, nodes, converters, etc..)
    import eagerx.converters # Registers SpaceConverters
    import eagerx.nodes      # Registers butterworth_filter
    import eagerx_ode        # Registers OdeBridge
    import eagerx_dcsc_setups.pendulum  # Registers Pendulum

    # Other
    import numpy as np
    import stable_baselines3 as sb


    if __name__ == "__main__":
        # Initialize node (& core if not already started)
        eagerx.initialize("eagerx_core", anonymous=True, log_level=eagerx.log.INFO)
        
        # Define simulation rate (Hz)
        rate = 30.0

        # Initialize empty graph
        graph = eagerx.Graph.create()

        # Show in the gui
        graph.gui()

        # Define bridge
        bridge = eagerx.Bridge.make(
            "OdeBridge",
            rate=rate,
            sync=True,
            real_time_factor=0,
            process=eagerx.process.NEW_PROCESS,
        )

        # Define step function
        def step_fn(prev_obs, obs, action, steps):
            state = obs["observation"][0]
            # Calculate reward
            sin_th, cos_th, thdot = state
            th = np.arctan2(sin_th, cos_th)
            cost = th**2 + 0.1 * (thdot / (1 + 10 * abs(th))) ** 2
            # Determine done flag
            done = steps > 500
            # Set info:
            info = dict()
            return obs, -cost, done, info

        # Initialize Environment
        env = Flatten(
            eagerx.EagerxEnv(name="rx", rate=rate, graph=graph, bridge=bridge, step_fn=step_fn)
        )
        env.render("human")

        # Train for 5 minutes
        model = sb.SAC("MlpPolicy", env, verbose=1)
        model.learn(total_timesteps=int(300 * rate))


.. note::
    For this example, the `eagerx_dcsc_setups package <https://github.com/eager-dev/eagerx_dcsc_setups>`_ should be installed.

Cite EAGERx
###########

If you are using EAGERx for your scientific publications, please cite:

.. code:: bibtex

    @article{eagerx,
        author  = {van der Heijden, Bas and Luijkx, Jelle, and Ferranti, Laura and Kober, Jens and Babuska, Robert},
        title = {EAGER: Engine Agnostic Gym Environment for Robotics},
        year = {2022},
        publisher = {GitHub},
        journal = {GitHub repository},
        howpublished = {\url{https://github.com/eager-dev/eagerx}}
    }

Credits
=======

The *eagerx_gui* package is heavily based on `pyqtgraph <https://github.com/pyqtgraph/pyqtgraph>`_.
The GUI is adapted from the implementation of the `pyqtgraph flowchart <https://github.com/pyqtgraph/pyqtgraph/tree/master/pyqtgraph/flowchart>`_.

Acknowledgements
=================
EAGERx is funded by the `OpenDR <https://opendr.eu/>`_ Horizon 2020 project.
