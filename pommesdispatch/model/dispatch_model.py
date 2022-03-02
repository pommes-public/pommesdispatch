# -*- coding: utf-8 -*-
"""
General description
-------------------
This is the dispatch variant of POMMES, the POwer Market Model
of Energy and reSources Department at TU Berlin.
The fundamental power market model has been originally developed
at TU Berlin and is now maintained by a developer group of alumni.
The source code is freely available under MIT license.
Usage of the model is highly encouraged. Contributing is welcome as well.

Repository, Documentation, Installation
---------------------------------------
All founds are hosted on
`GitHub <https://github.com/pommes-public/pommesdispatch>`_

To install, simply type ``pip install pommesdispatch``

Please find the documentation `here <https://pommesdispatch.readthedocs.io/>`_

Licensing information and Disclaimer
------------------------------------
This software is provided under MIT License (see licensing file).

A special thank you goes out to all the developers creating,
maintaining, and expanding packages used in this model,
especially to the oemof and pyomo developer groups!

In addition to that, a special thank you goes to all students
and student assistants which have contributed to the model itself
or its data inputs.

Input Data
----------
Input data can be compiled using the ``pommesdata`` package.
A precompiled version is distributed with the dispatch model.

Installation requirements
-------------------------
See `environments.yml` file

@author: Johannes Kochems (*), Yannick Werner (*), Johannes Giehl,
Benjamin Grosse

Contributors:
Sophie Westphal, Flora von Mikulicz-Radecki, Carla Spiller, Fabian Büllesbach,
Timona Ghosh, Paul Verwiebe, Leticia Encinas Rosa, Joachim Müller-Kirchenbauer

(*) Corresponding authors
"""

import argparse
import logging
import time

import pandas as pd
import yaml
from oemof.solph import processing
from oemof.solph import views
from yaml.loader import SafeLoader

from pommesdispatch.model_funcs import model_control


def run_dispatch_model(config_file="./config.yml"):
    """
    Run a pommesdispatch model.

    Read in config information from a yaml file, initialize and run a
    dispatch model and process results.

    Parameters
    ----------
    config_file: str
        A file holding the necessary configuration information for
        a pommesdispatch model
    """
    # ---- MODEL CONFIGURATION ----

    # Import model config from yaml config file
    with open(config_file) as file:
        config = yaml.load(file, Loader=SafeLoader)

    dm = model_control.DispatchModel()
    dm.update_model_configuration(
        config["control_parameters"],
        config["time_parameters"],
        config["input_output_parameters"],
        nolog=True,
    )

    if dm.rolling_horizon:
        dm.add_rolling_horizon_configuration(
            config["rolling_horizon_parameters"], nolog=True
        )

    dm.initialize_logging()
    dm.check_model_configuration()
    dm.show_configuration_log()

    # ---- MODEL RUN ----

    # Initialize model meta information and results DataFrames
    model_meta = {
        "overall_objective": 0,
        "overall_time": 0,
        "overall_solution_time": 0,
    }
    ts = time.gmtime()
    dispatch_results = pd.DataFrame()
    power_prices = pd.DataFrame()

    # Model run for integral optimization horizon (simple model set up)
    if not dm.rolling_horizon:
        dm.build_simple_model()

        dm.om.receive_duals()
        logging.info(
            "Obtaining dual values and reduced costs from the model\n"
            "in order to calculate power prices."
        )

        if dm.write_lp_file:
            dm.om.write(
                dm.path_folder_output + "pommesdispatch_model.lp",
                io_options={"symbolic_solver_labels": True},
            )
        dm.om.solve(solver=dm.solver, solve_kwargs={"tee": True})
        meta_results = processing.meta_results(dm.om)

        power_prices = dm.get_power_prices_from_duals()

        model_meta["overall_objective"] = meta_results["objective"]
        model_meta["overall_solution_time"] += meta_results["solver"]["Time"]

    # Model run for rolling horizon optimization
    if dm.rolling_horizon:
        logging.info(
            "Creating a LP optimization model for dispatch optimization\n"
            "using a ROLLING HORIZON approach for model solution."
        )

        # Initialization of rolling horizon model run
        iteration_results = {
            "storages_initial": pd.DataFrame(),
            "model_results": {},
            "dispatch_results": dispatch_results,
            "power_prices": power_prices,
        }

        for counter in range(getattr(dm, "amount_of_time_slices")):
            # rebuild the EnergySystem in each iteration
            dm.build_rolling_horizon_model(counter, iteration_results)

            # Solve rolling horizon model
            dm.solve_rolling_horizon_model(
                counter, iteration_results, model_meta
            )

            # Get initial states for the next model run from results
            dm.retrieve_initial_states_rolling_horizon(iteration_results)

        dispatch_results = iteration_results["dispatch_results"]
        power_prices = iteration_results["power_prices"]

    model_meta["overall_time"] = time.mktime(time.gmtime()) - time.mktime(ts)

    # ---- MODEL RESULTS PROCESSING ----

    model_control.show_meta_logging_info(model_meta)

    if not dm.rolling_horizon:
        model_results = processing.results(dm.om)

        buses_el_views = [country + "_bus_el" for country in dm.countries]
        dispatch_results = pd.concat(
            [
                views.node(model_results, bus_el)["sequences"]
                for bus_el in buses_el_views
            ],
            axis=1,
        )

    if dm.save_updated_market_values:
        (
            market_values,
            market_values_hourly,
        ) = dm.calculate_market_values_from_model(power_prices)
        market_values.to_csv(
            dm.path_folder_output
            + getattr(dm, "filename")
            + "_monthly_market_values.csv",
            sep=",",
            decimal=".",
        )

        market_values_hourly.to_csv(
            dm.path_folder_input
            + "costs_market_values"
            + "_"
            + str(dm.year)
            + ".csv",
            sep=",",
            decimal=".",
        )

    if dm.save_production_results:
        dispatch_results.to_csv(
            dm.path_folder_output
            + getattr(dm, "filename")
            + "_production.csv",
            sep=",",
            decimal=".",
        )

    if dm.save_price_results:
        power_prices.to_csv(
            dm.path_folder_output
            + getattr(dm, "filename")
            + "_power-prices.csv",
            sep=",",
            decimal=".",
        )


def add_args():
    """Add command line argument for config file"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-f",
        "--file",
        required=False,
        default="./config.yml",
        help="Specify input config file",
    )
    parser.add_argument(
        "--init",
        required=False,
        action="store_true",
        help="Automatically generate default config",
    )
    parser.add_argument(
        "--iterations",
        metavar="n",
        type=int,
        required=False,
        default=1,
        help="Define number of iterations for market value update",
    )
    args = parser.parse_args()
    return args
