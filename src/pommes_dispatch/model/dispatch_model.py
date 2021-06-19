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

Git And Documentation
---------------------
The project files contain extensive DocString as well as inline comments.
For additional information, see the wiki: 
https://git.tu-berlin.de/POMMES/POMMES/wikis/home

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
Input data can be compiled using the POMMES_data package.
A precompiled version is distributed with the dispatch model.

Installation requirements
-------------------------
Python version >= 3.8
oemof version 0.4.4


@author: Johannes Kochems (*), Yannick Werner (*), Johannes Giehl,
Benjamin Grosse

Contributors:
Sophie Westphal, Flora von Mikulicz-Radecki, Carla Spiller, Fabian Büllesbach,
Timona Ghosh, Paul Verwiebe, Leticia Encinas Rosa, Joachim Müller-Kirchenbauer

(*) Corresponding authors
"""

import calendar
import logging
import time

import pandas as pd
from oemof.solph import processing
from oemof.solph import views

from pommes_dispatch.model_funcs import model_control

# ---- MODEL SETTINGS ----
# THIS IS THE ONLY PART, THE USER CAN MANIPULATE

# 1) Determine model configuration through control parameters

control_parameters = {
    "rolling_horizon": False,
    "aggregate_input": False,
    "countries": ['AT', 'BE', 'CH', 'CZ', 'DE', 'DK1', 'DK2', 'FR', 'NL',
                  'NO1', 'NO2', 'NO3', 'NO4', 'NO5', 'PL',
                  'SE1', 'SE2', 'SE3', 'SE4'],
    "solver": "gurobi",
    "fuel_cost_pathway": "middle",
    "activate_emissions_limit": False,
    "emissions_pathway": "100_percent_linear",
    "activate_demand_response": False,
    "demand_response_approach": "DLR",
    "demand_response_scenario": "50",
    "save_production_results": True,
    "save_price_results": True,
}

# 2) Set model optimization time and frequency for simple model runs

time_parameters = {
    "start_time": "2017-01-01 00:00:00",
    "end_time": "2017-01-01 23:00:00",
    "freq": "60min"
}

# 3) Set input and output data paths

io_parameters = {
    "path_folder_input": "../../../inputs/",
    "path_folder_output": "../../../results/"
}

# 4) Set rolling horizon parameters (optional)

rh_parameters = {
    "timeslice_length_wo_overlap_in_hours": 24,
    "overlap_in_hours": 12
}

dm = model_control.DispatchModel()
dm.update_model_configuration(
    control_parameters,
    time_parameters,
    io_parameters,
    nolog=True)

# TODO: Use same procedure for data input for rolling horizon as well
if dm.rolling_horizon:
    dm.add_rh_configuration(rh_parameters)

dm.initialize_logging()
dm.check_model_configuration()
dm.show_configuration_log()

# ---- MODEL RUN ----
# NO NEED FOR USER CHANGES FROM HERE ON

# Initialize results and meta information
model_meta = {
    "overall_objective": 0,
    "overall_time": 0,
    "overall_solution_time": 0
}
ts = time.gmtime()
results = None
power_prices = pd.DataFrame()

# Model run for simple model set up
if not dm.rolling_horizon:
    dm.build_simple_model()

    dm.om.receive_duals()
    logging.info("Obtaining dual values and reduced costs from the model\n"
                 "in order to calculate power prices.")

    dm.om.solve(solver=dm.solver, solve_kwargs={"tee": True})
    meta_results = processing.meta_results(dm.om)

    ts_2 = time.gmtime()
    power_prices = dm.get_power_prices_from_duals()

    model_meta["overall_objective"] = meta_results["objective"]
    model_meta["overall_solution_time"] += meta_results["solver"]["Time"]
    model_meta["overall_time"] = time.mktime(ts_2) - time.mktime(ts)

# Rolling horizon: Run LP model
if dm.rolling_horizon:
    logging.info('Creating a LP optimization model for dipatch optimization \n'
                 'using a ROLLING HORIZON approach for model solution.')

    # Initialization of RH model run 
    counter = 0
    storages_init_df = pd.DataFrame()
    results = pd.DataFrame()
    power_prices = pd.DataFrame()

    for counter in range(amount_of_timeslices):
        # rebuild the EnergySystem in each iteration
        (om, es, timeseries_start, storage_labels,
         datetime_index) = model_control.build_RH_model(
            path_folder_input,
            AggregateInput,
            countries,
            fuel_cost_pathway,
            timeseries_start,
            timeslice_length_wo_overlap_in_timesteps,
            timeslice_length_with_overlap,
            counter,
            storages_init_df,
            freq,
            str(year),
            ActivateEmissionsLimit,
            emissions_pathway,
            ActivateDemandResponse,
            approach,
            scenario)

        # Solve RH model and return results
        (om, model_results, results, overall_objective,
         overall_solution_time, power_prices) = model_control.solve_RH_model(
            om,
            datetime_index,
            counter,
            timeslice_length_wo_overlap_in_timesteps,
            timeslice_length_with_overlap,
            results,
            power_prices,
            overall_objective,
            overall_solution_time,
            solver=solver)

        # Get initial states for the next model run
        storages_init_df = model_control.initial_states_RH(
            model_results,
            timeslice_length_wo_overlap_in_timesteps,
            storage_labels)

        ts_2 = time.gmtime()
        overall_time = calendar.timegm(ts_2) - calendar.timegm(ts)

# ---- PROCESS MODEL RESULTS ----

dm.show_meta_logging_info(model_meta)

if not dm.rolling_horizon:
    model_results = processing.results(dm.om)

    buses_el_views = [country + '_bus_el' for country in dm.countries]
    results = pd.concat([views.node(model_results, bus_el)['sequences']
                         for bus_el in buses_el_views], axis=1)

if dm.save_production_results:
    results.to_csv(dm.path_folder_output + getattr(dm, "filename")
                   + '_production.csv', sep=',', decimal='.')

if dm.save_price_results:
    power_prices.to_csv(
        dm.path_folder_output + getattr(dm, "filename")
        + '_power-prices.csv', sep=',', decimal='.')
