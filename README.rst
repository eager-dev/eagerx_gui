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
EAGERx (Engine Agnostic Graph Environments for Robotics) enables users to easily define new tasks, switch from one sensor to another, and switch from simulation to reality with a single line of code by being invariant to the physics engine.

`The core repository is available here <https://github.com/eager-dev/eagerx>`_.

`Full documentation and tutorials (including package creation and contributing) are available here <https://eagerx.readthedocs.io/en/master/>`_.

Installation
############

You can install the package using pip:

.. code:: shell

    pip3 install eagerx-gui

Cite EAGERx
###########

If you are using EAGERx for your scientific publications, please cite:

.. code:: bibtex
   @article{van2024eagerx,
     title={EAGERx: Graph-Based Framework for Sim2real Robot Learning},
     author={van der Heijden, Bas and Luijkx, Jelle and Ferranti, Laura and Kober, Jens and Babuska, Robert},
     journal={arXiv preprint arXiv:2407.04328},
     year={2024}
   }

Credits
#######

The *eagerx_gui* package is heavily based on `pyqtgraph <https://github.com/pyqtgraph/pyqtgraph>`_.
The GUI is adapted from the implementation of the `pyqtgraph flowchart <https://github.com/pyqtgraph/pyqtgraph/tree/master/pyqtgraph/flowchart>`_.

Acknowledgements
################

EAGERx is funded by the `OpenDR <https://opendr.eu/>`_ Horizon 2020 project.
