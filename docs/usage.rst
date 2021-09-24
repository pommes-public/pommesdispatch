Installation and User's guide
=============================

.. contents::


Installation
------------
To set up ``pommesdispatch``, you have to set up a virtual environment
(e.g. using conda) or add the required packages to your python installation.
This is taken care of by the pip installation. When you clone the environment,
you have to install the packages for the requirements file (see :ref:`setup`).

Additionally, you have to install a solver in order to solve
the mathematical optimization problem (see :ref:`solver`).

.. _setup:

Setting up the environment
++++++++++++++++++++++++++
``pommesdispatch`` is hosted on `PyPI <https://pypi.org/>`_.
To install it, please use the following command

.. code::

    pip install pommesdispatch


If you want to contribute as a developer, you fist have to
`fork <https://docs.github.com/en/get-started/quickstart/fork-a-repo>`_
it and then clone the environment, in order to copy the files locally by typing

.. code::

    git clone https://github.com/your-github-username/pommesdispatch.git

| After cloning the repository, you have to install the required dependencies.
 Make sure you have conda installed as a package manager.
 If not, you can download it `here <https://www.anaconda.com/>`_.
| Open a command shell and navigate to the folder
 where you copied the environment to.
| Use the following command to install dependencies

.. code::

    conda env create -f environment.yml

Activate your environment by typing

.. code::

    conda activate pommes_dispatch

.. _solver:

Installing a solver
+++++++++++++++++++
In order to solve a ``pommesdispatch`` model instance,
you need a solver installed.
Please see
`oemof.solph's information on solvers <https://github.com/oemof/oemof-solph#installing-a-solver>`_.
As a default, gurobi is used for ``pommesdispatch`` models.
It is a commercial solver, but provides academic licenses, though,
if this applies to you. Elsewise, we recommend to use CBC
as the solver oemof recommends. To test your solver
and oemof.solph installation,
again see information from
`oemof.solph <https://github.com/oemof/oemof-solph#installation-test>`_.

.. _using:

Using pommesdispatch
---------------------

Providing input data
++++++++++++++++++++

You can obtain pommes input data either by

* extracting `this .zip file <https://myfantasyzipfile.com>`_ which has
  been created using ``pommesdata`` or
* from running ``pommesdata`` which you can find
  `in this repository <https://github.com/pommes-public/pommesdata>`_

``pommesdata`` provides input data for simulating years between 2017 and 2030.
Once you have run it, you have to copy the output of ``pommesdata`` which
is stored in the folder "prepared_data"
to the "inputs" folder of ``pommesdispatch``. You should now have a bunch
of .csv files with the oemof.solph components names in their file name.

Whe using ``pommesdata``, feel free to adjust assumptions on
the power plant park, according to your needs.

.. _config:

Configuring the model
+++++++++++++++++++++

We provide a default model configuration coming with the installation.
To make use of this, you have to run a console script by typing

.. code::

    run_pommes_dispatch --init

Once you have created the config file, you can adjust it to your needs.
If you do not wish to do so and use the default, you can skip this section
and move right to the next one, :ref:`running`.

You'll find dictionary-alike hierarchical entries in the ``config.yml``
file which control the simulation.
In the first section, you can change general model settings, e.g. if
you want to use another solver or if you want to run a rolling horizon
model. You can play around with the boolean values, but we recommend to
keep the parameters for storing result files, i.e.
``save_production_results`` and ``save_price_results`` set to True.

Pay attention to the allowed values for the string values:

- ``countries``: The maximum of countries allowed is the default. You can just
  remove countries if you wish to have a smaller coverage
- ``fuel_cost_pathway``: allowed values are *lower*, *middle* and *upper* for
  a rather low, middle or rather high future fuel costs increase
- ``emissions_pathway``: allowed values are *BAU*, *80_percent_linear*,
  *95_percent_linear* or *100_percent_linear*,
  describing the emissions reduction path for the German power sector
  by a historic trend extrapolation (linear regression), an 80%
  reduction path until 2050, a 95% reduction path until 2050
  or a 100% reduction path until 2045.
- ``demand_response_approach``: allowed values are *DLR*, *DIW* and *oemof*.
  These describe different options for demand response modeling implemented in
  oemof.solph, see `this oemof.solph module <https://github.com/oemof/oemof-solph/blob/dev/src/oemof/solph/custom/sink_dsm.py>`_
  and an `comparison of approaches from the INREC 2020 <https://github.com/jokochems/DR_modeling_oemof/blob/master/Kochems_Demand_Response_INREC.pdf>`_
  for details.

.. code:: yaml

    # 1) Set overall workflow control parameters
    control_parameters:
        rolling_horizon: False
        aggregate_input: False
        countries: ['AT', 'BE', 'CH', 'CZ', 'DE', 'DK1', 'DK2', 'FR', 'NL',
                    'NO1', 'NO2', 'NO3', 'NO4', 'NO5', 'PL',
                    'SE1', 'SE2', 'SE3', 'SE4']
        solver: "gurobi"
        fuel_cost_pathway: "middle"
        activate_emissions_limit: False
        emissions_pathway: "100_percent_linear"
        activate_demand_response: False
        demand_response_approach: "DLR"
        demand_response_scenario: "50"
        save_production_results: True
        save_price_results: True

.. note::
    | Including an emissions limit usually leads to an infeasible model formulation.
    | This is because we specify minimum loads for power plants causing emissions
    | exceeding the limit imposed. If you wish to include an emissions limit, you
    | should adjust minimum loads. This is only recommended for experienced users.
    | To enforce emissions reductions, setting higher CO2 prices is another option
    | rather than constraining the amount of emissions.

In the next section, you can control the simulation time. Please stick
to the date format (pre-)defined. You have to ensure that the input data
time series match the time frame you want to simulate. As a default, you'll
find data for 2017 and 2030.

.. code:: yaml

    # 2) Set model optimization time and frequency
    time_parameters:
        start_time: "2017-01-01 00:00:00"
        end_time: "2017-01-02 23:00:00"
        freq: "60min"

In the third section, you specify where your inputs and outputs are stored.
You can use the default values here. Please ensure that you have provided
the necessary input data.

.. code:: yaml

    # 3) Set input and output data paths
    input_output_parameters:
        path_folder_input: "./inputs/"
        path_folder_output: "./results/"

The last section is only applicable if you want to run a rolling
horizon simulation, see :ref:`rolling-horizon` for background information
if you are not familiar with the concept.

- ``time_slice_length_wo_overlap_in_hours`` defines the length of a time slice
  excluding the overlap in hours
- ``overlap_in_hours`` is the length of the overlap in hours, i.e. the number
  of hours that will be dropped and are only introduced to prevent end-time
  effects.

.. code:: yaml

    # 4) Set rolling horizon parameters (optional)
    rolling_horizon_parameters:
        time_slice_length_wo_overlap_in_hours: 24
        overlap_in_hours: 12

.. _running:

Running the model
+++++++++++++++++
Once you have configured your model, running it is fairly simple.

You can directly run the console script ``run_pommes_dispatch``
in a command line shell by typing

.. code::

    run_pommes_dispatch <-f "path-to-your-config-file.yml">

You may leave out the specification for the YAML file.
This will lead to using the ``config.yml`` file you have created when
initializing the config.

Whe you run the script, you'll see
some logging information on the console when your run the model.
Once the model run is finished, you can find, inspect, analyze and plot your
results in the results folder (or the folder you have specified to store
model results).

Another way is to run ``pommes_dispatch.py`` in your python editor of choice
(we recommend `PyCharm <https://www.jetbrains.com/pycharm/>`_).
In this case, you have to specify the path to your config file as a run
argument ``-f ../../config.yml``.
Also, in the config file, you have to specify the relative
relations to the input and output folder, so you probably have to replace
``./inputs`` with ``../../inputs`` and ``./outputs`` with ``../../ouputs``.
