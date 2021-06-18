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
Input data is read in from the repository POMMES_data using dependencies

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
import math
import time

import pandas as pd
from oemof.solph import processing
from oemof.solph import views
from oemof.tools import logger

from pommes_dispatch.model_funcs import model_control

# ---- MODEL SETTINGS ----

# 1) Determine model configuration through control variables

# Control main settings
# TODO: Resume idea of putting everything to control kwargs passed to funcs
model_parameters = {
    "RollingHorizon": False,
    "AggregateInput": False,
    "countries": ['AT', 'BE', 'CH', 'CZ', 'DE', 'DK1', 'DK2', 'FR', 'NL',
                  'NO1', 'NO2', 'NO3', 'NO4', 'NO5', 'PL',
                  'SE1', 'SE2', 'SE3', 'SE4'],
    "solver": "gurobi",
    "fuel_cost_pathway": "middle",
    "ActivateEmissionsLimit": False,
    "emission_pathway": "100_percent_linear",
    "ActivateDemandResponse": False,
    "approach": "DLR",
    "scenario": "50",
    "SaveProductionResults": True,
    "SavePriceResults": True,
}

RollingHorizon = False
AggregateInput = False
countries = ['AT', 'BE', 'CH', 'CZ', 'DE', 'DK1', 'DK2', 'FR', 'NL', 'NO1',
             'NO2', 'NO3', 'NO4', 'NO5', 'PL', 'SE1', 'SE2', 'SE3', 'SE4']
solver = 'gurobi'

# Control cost pathways (options: lower, middle, upper)
fuel_cost_pathway = 'middle'

# Control emissions limit (options: BAU, 80_percent_linear,
# 95_percent_linear, 100_percent_linear)
ActivateEmissionsLimit = False
emission_pathway = '100_percent_linear'

# Control Demand response modeling
# options for approach: ['DIW', 'DLR', 'oemof']
# options for scenario: ['25', '50', '75']
ActivateDemandResponse = False
approach = 'DLR'
scenario = '50'

# Control processing of outputs
SaveProductionResults = True
SavePriceResults = True

# 2) Set model optimization time and frequency for simple model runs

time_parameters = {
    "starttime": "2017-01-01 00:00:00",
    "endtime": "2017-01-02 23:00:00",
    "freq": "60min"
}

# Control starttime and endtime for simulation
starttime = '2017-01-01 00:00:00'
endtime = '2017-01-02 23:00:00'
freq = '60min'
year = pd.to_datetime(starttime).year

# Control rolling horizon timeslice length

RH_parameters = {
    "timeslice_length_wo_overlap_in_hours": 24,
    "overlap_in_hours": 12
}

if RollingHorizon:
    timeslice_length_wo_overlap_in_hours = 24
    overlap_in_hours = 12

# Meta information (No need to change anything here)
ts = time.gmtime()
timestamp = time.strftime("%Y-%m-%d_%H-%M-%S", ts)
overall_objective = 0
overall_time = 0
overall_solution_time = 0
# optimization_timeframe = days_between(starttime, endtime)
optimization_timeframe = 300

# Create filename that covers relevant model information
basic_filename = 'dispatch_LP_'

if not RollingHorizon:
    RH = 'simple_'
else:
    RH = 'RH_'
if AggregateInput:
    Agg = 'clustered_'
else:
    Agg = 'complete_'

filename = (basic_filename + "start-" + starttime[:10] + "_"
            + str(optimization_timeframe) + "-days_" + RH + Agg)

logger.define_logging(logfile=filename + '.log')

# 3) Set input data

# path_folder_output folder where all input data is stored
path_folder_input = "../../../inputs/"
path_folder_output = "../../../results/"

# Show some logging info dependent on model configuration
if AggregateInput:
    logging.info('Using the AGGREGATED POWER PLANT DATA SET')
else:
    logging.info('Using the COMPLETE POWER PLANT DATA SET.\n'
                 'Minimum power output constraint of (individual)\n'
                 'transformers will be neglected.')

if ActivateDemandResponse:
    logging.info('Using approach from {} for DEMAND RESPONSE modeling\n'
                 'Considering a {}% scenario'.format(approach, scenario))
else:
    logging.info('Running a model WITHOUT DEMAND RESPONSE')

# Calculate timeslice and model control information for Rolling horizon

if RollingHorizon:
    # TODO: Use same procedure for data input for rolling horizon as well
    timeseries_start = pd.Timestamp(starttime, freq)
    timeseries_end = pd.Timestamp(endtime, freq)
    timeslice_length_wo_overlap_in_timesteps = (
            {'60min': 1, '15min': 4}[freq]
            * timeslice_length_wo_overlap_in_hours)
    overlap_in_timesteps = ({'60min': 1, '15min': 4}[freq]
                            * overlap_in_hours)
    timeslice_length_with_overlap = (
            timeslice_length_wo_overlap_in_timesteps
            + overlap_in_timesteps)
    overall_timesteps = timesteps_between_timestamps(
        timeseries_start, timeseries_end, freq)
    amount_of_timeslices = math.ceil(
        overall_timesteps
        / timeslice_length_wo_overlap_in_timesteps)

# ---- MODEL RUN ----

# Model run for simple model set up

if not RollingHorizon:
    # Build the mathematical optimization model
    om = model_control.build_simple_model(
        path_folder_input,
        AggregateInput,
        countries,
        fuel_cost_pathway,
        starttime,
        endtime,
        freq,
        str(year),
        ActivateEmissionsLimit,
        emission_pathway,
        ActivateDemandResponse,
        approach,
        scenario)

    om.receive_duals()
    logging.info('Obtaining dual values and reduced costs from the model\n'
                 'in order to calculate power prices.')

    om.solve(solver=solver, solve_kwargs={'tee': True})
    meta_results = processing.meta_results(om)
    overall_solution_time += meta_results['solver']['Time']

    ts_2 = time.gmtime()
    overall_time = time.mktime(ts_2) - time.mktime(ts)

    power_prices = model_control.get_power_prices_from_duals(
        om, pd.date_range(starttime, endtime, freq=freq))

    print("********************************************************")
    logging.info("Done!")
    print(f'Overall solution time: {overall_solution_time:.2f}')
    print(f'Overall time: {overall_time:.2f}')

# Rolling horizon: Run LP model

if RollingHorizon:
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
            emission_pathway,
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

    print('**********************FINALLY DONE**********************')
    print(f'Overall objective value: {overall_objective:.2f}')
    print(f'Overall solution time: {overall_solution_time:.2f}')
    print(f'Overall time: {overall_time:.2f}')

# ---- PROCESS MODEL RESULTS ----

if not RollingHorizon:
    model_results = processing.results(om)

    buses_el_views = [country + '_bus_el' for country in countries]
    results = pd.concat([views.node(model_results, bus_el)['sequences']
                         for bus_el in buses_el_views], axis=1)

if SaveProductionResults:
    results.to_csv(path_folder_output + filename + '_production.csv',
                   sep=',', decimal='.')

if SavePriceResults:
    power_prices.to_csv(path_folder_output + filename + '_power-prices.csv',
                        sep=';', decimal=',')
