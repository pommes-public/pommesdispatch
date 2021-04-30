# -*- coding: utf-8 -*-
"""
General desription
------------------
This file contains all function definitions for reading in input data
used for the fundamental model for power market optimization modeling
from the Department Energy and Resources at TU Berlin.

These functions are imported by the main project file.

@author: Johannes Kochems (*), Yannick Werner (*), Johannes Giehl,
Fabian Büllesbach, Carla Spiller, Sophie Westphal

(*) Corresponding authors
"""

import logging

import pandas as pd
import pyomo.environ as po
from oemof.solph import (constraints, views,
                         models, network, processing)

from data_input import nodes_from_csv, nodes_from_csv_rh
from functions_for_processing_of_outputs_LP import get_power_prices_from_duals


def add_further_constrs(om,
                        ActivateEmissionsLimit,
                        emissions_limit,
                        countries=None,
                        fuels=None):
    """Integrate further constraints into the optimization model

    For now, an additional overall emissions limit can be imposed.

    Note that setting an emissions limit may conflict with high minimum
    loads from conventional transformers. This may lead to model infeasibility
    if commodity bus balances cannot be met.
    
    Parameters
    ----------
    om : :class:`oemof.solph.models.Model`
        The original mathematical optimisation model to be solved

    ActivateEmissionsLimit : :obj:`boolean`
        If True, an emission limit is introduced

    emissions_limit : float
        The actual emissions limit to be used

    countries : :obj:`list` of `str`
        The countries for which an emissions limit shall be imposed
        (Usually only Germany)

    fuels : :obj:`list` of `str`
        The fuels for which an emissions limit shall be imposed

    """

    if countries is None:
        countries = ['DE']

    if fuels is None:
        fuels = ['biomass', 'hardcoal', 'lignite',
                 'natgas', 'uranium', 'oil',
                 'otherfossil', 'waste', 'mixedfuels']

    # Emissions limit is imposed for flows from commodity source to commodity bus
    emission_flow_labels = [country + '_bus_' + fuel
                            for country in countries
                            for fuel in fuels]

    emission_flows = {}

    for (i, o) in om.flows:
        if any(x in o.label for x in emission_flow_labels):
            emission_flows[(i, o)] = om.flows[(i, o)]

    if ActivateEmissionsLimit:
        constraints.emission_limit(om, flows=emission_flows,
                                   limit=emissions_limit)
        logging.info(f"Adding an EMISSIONS LIMIT of {emissions_limit} t CO2")


def build_simple_model(path_folder_input,
                       AggregateInput,
                       countries,
                       fuel_cost_pathway,
                       starttime='2017-01-01 00:00:00',
                       endtime='2017-01-02 12:00:00',
                       freq='60min',
                       year=2017,
                       ActivateEmissionsLimit=False,
                       emission_pathway='100_percent_linear',
                       ActivateDemandResponse=False,
                       approach='DIW',
                       scenario='50'):
    """Set up and return a simple model (i.e. an overall optimization run
    not including any measures for complexity reduction). 
    
    Parameters
    ----------
    path_folder_input : :obj:`str`
        The path folder where the input data is stored

    AggregateInput : boolean
        If True, an aggregated input data set is used

    countries : list of str
        List of countries to be simulated

    fuel_cost_pathway : `str`
        The fuel costs pathway to be used ('lower', 'middle', 'upper')

    starttime : :obj:`str`
        The starttime of the optimization run
    
    endtime : :obj:`str`
        The endtime of the optimization run

    freq : :obj:`str`
        The frequency of the timeindex

    year : int
        The simulation year

    ActivateEmissionsLimit : :obj:`boolean`
        If True, an emission limit is introduced

    emission_pathway : str
        The pathway for emissions reduction to be used

    ActivateDemandResponse : :obj:`boolean`
        If True, demand response input data is read in

    approach : :obj:`str`
        The modeling approach to be used for demand response modeling

    scenario : :obj:`str`
        The scenario to be used for demand response modeling
    
    Returns
    -------
    om : :class:`oemof.colph.models.Model`
        The mathematical optimisation model to be solved  
        
    """
    logging.info('Starting optimization')
    logging.info('Running a DISPATCH OPTIMIZATION')

    datetime_index = pd.date_range(
        starttime, endtime, freq=freq)
    es = network.EnergySystem(timeindex=datetime_index)

    nodes_dict, emissions_limit = nodes_from_csv(
        path_folder_input,
        AggregateInput,
        countries,
        fuel_cost_pathway,
        starttime,
        endtime,
        year,
        ActivateEmissionsLimit,
        emission_pathway,
        ActivateDemandResponse,
        approach,
        scenario)

    logging.info('Creating a LP model for DISPATCH OPTIMIZATION.')

    es.add(*nodes_dict.values())
    om = models.Model(es)

    add_further_constrs(
        om,
        ActivateEmissionsLimit,
        emissions_limit)

    return om


def get_power_prices_from_duals(om, datetime_index):
    """ Function to obtain the power price results for a LP model formulation
    (dispatch) from the dual value of the Bus.balance constraint of the
    electricity bus. NOTE: Prices are other than 0 if constraint is binding
    and equal to 0 if constraint is not binding, i.e. if plenty of production
    surplus is available at no cost.

    Parameters:
    -----------
    om: :class:`oemof.solph.models.Model`
        The mathematical model formulation (including its dual values)

    datetime_index: :obj:`pd.date_range`
        The datetime_index of the energy system

    Returns:
    --------
    power_prices: :obj:`pd.DataFrame`

    """

    constr = [c for c in om.component_objects(po.Constraint, active=True)
              if c.name == "Bus.balance"][0]

    power_prices_list = [om.dual[constr[index]] for index in constr if
                         index[0].label == "DE_bus_el"]
    power_prices = pd.DataFrame(data=power_prices_list, index=datetime_index,
                                columns=["Power price"])

    return power_prices


def initial_states_RH(model_results,
                      timeslice_length_wo_overlap_in_timesteps,
                      storage_labels):
    """Obtain the initial states for the upcoming rolling horizon model run
    
    Parameters
    ----------                          
    model_results: :obj:`pd.DataFrame`
        the results of the optimization run
                          
    timeslice_length_wo_overlap_in_timesteps: :obj:`int`
        length of a rolling horizon timeslice excluding overlap
                          
    storage_labels: :obj:`list` of :class:`str`
        list of storage labels (obtained from input data)
    
    Returns
    -------
    storages_init_df : :obj:`pd.DataFrame`
        A pd.DataFrame containing the storage data (i.e. statuses for
        the last timestep of the optimization window - excluding overlap)
        
    """

    storages_init_df = pd.DataFrame(columns=['Capacity_Last_Timestep'],
                                    index=storage_labels)

    for i, s in storages_init_df.iterrows():
        storage = views.node(model_results, i)

        storages_init_df.loc[i, 'Capacity_Last_Timestep'] = (
            storage['sequences'][((i, 'None'), 'storage_content')][
                timeslice_length_wo_overlap_in_timesteps - 1])

    logging.info("Obtained initial (storage) states for next iteration")

    return storages_init_df


def build_RH_model(path_folder_input,
                   AggregateInput,
                   countries,
                   fuel_cost_pathway,
                   timeseries_start,
                   timeslice_length_wo_overlap_in_timesteps,
                   timeslice_length_with_overlap,
                   counter,
                   storages_init_df,
                   freq,
                   year,
                   ActivateEmissionsLimit,
                   emission_pathway,
                   ActivateDemandResponse,
                   approach,
                   scenario):
    """ Set up and return a rolling horizon LP dispatch model

    Parameters
    ----------
    path_folder_input : :obj:`str`
        The path folder where the input data is stored

    AggregateInput : boolean
        If True, an aggregated input data set is used

    countries : list of str
        List of countries to be simulated

    fuel_cost_pathway : `str`
        The fuel costs pathway to be used ('lower', 'middle', 'upper')

    timeseries_start : :obj:`pd.Timestamp`
        the adjusted starting timestep for used the next iteration

    timeslice_length_wo_overlap_in_timesteps : :obj:`int`
        The timeslice length without the overlap (in timesteps)

    timeslice_length_with_overlap : :obj:`int`
        The timeslice length with the overlap (in timesteps)

    counter: :obj:`int`
        A counter for rolling horizon optimization windows (iterations)

    storages_init_df : :obj:`pd.DataFrame`
        A pd.DataFrame containing the storage data (i.e. statuses for
        the last timestep of the optimization window - excluding overlap)

    freq : :obj:`str`
        The frequency of the timeindex

    year : int
        The simulation year

    ActivateEmissionsLimit : :obj:`boolean`
        If True, an emission limit is introduced

    emission_pathway : str
        The pathway for emissions reduction to be used

    ActivateDemandResponse : :obj:`boolean`
        If True, demand response input data is read in

    approach : :obj:`str`
        The modeling approach to be used for demand response modeling

    scenario : :obj:`str`
        The scenario to be used for demand response modeling

    Returns
    -------
    om : :class:`oemof.solph.models.Model`
        The mathematical optimisation model to be solved

    es : :class:`oemof.solph.network.EnergySystem`
        The energy system itself (used for determining initial states for the
        next rolling horizon iteration)

    timeseries_start : :obj:`pd.Timestamp`
        the adjusted starting timestep for used the next iteration

    datetime_index : :obj:`pd.DatetimeIndex`
        The datetime index of the EnergySystem for the next iteration

    storage_labels: :obj:`list` of :class:`str`
        list of storage labels (obtained from input data)
    """
    timeseries_end = timeseries_start + pd.to_timedelta(
        timeslice_length_wo_overlap_in_timesteps, 'h')

    logging.info(f'Starting optimization for optimization run {counter}')
    logging.info(f'Start of iteration {counter}: {timeseries_start}')
    logging.info(f'End of iteration {counter}: {timeseries_end}')

    datetime_index = pd.date_range(start=timeseries_start,
                                   periods=timeslice_length_with_overlap,
                                   freq=freq)
    es = network.EnergySystem(timeindex=datetime_index)

    node_dict, storage_labels, emissions_limit = nodes_from_csv_rh(
        path_folder_input,
        AggregateInput,
        countries,
        timeseries_start,
        timeslice_length_with_overlap,
        storages_init_df,
        freq,
        fuel_cost_pathway,
        year,
        ActivateEmissionsLimit,
        emission_pathway,
        ActivateDemandResponse,
        approach,
        scenario)

    timeseries_start = timeseries_end

    es.add(*node_dict.values())
    logging.info(f"Sucessfully set up energy system for iteration {counter}")

    om = models.Model(es)

    add_further_constrs(
        om,
        ActivateEmissionsLimit,
        emissions_limit)

    return om, es, timeseries_start, storage_labels, datetime_index


def solve_RH_model(om,
                   datetime_index,
                   counter,
                   timeslice_length_wo_overlap_in_timesteps,
                   timeslice_length_with_overlap,
                   results,
                   power_prices,
                   overall_objective,
                   overall_solution_time,
                   solver='gurobi'):
    """Solve an Rolling Horizon optimization model and return its results
    
    Parameters
    ----------
    om : :class:`oemof.solph.models.Model`
        The mathematical optimisation model to be solved

    datetime_index : :obj:`pd.DatetimeIndex`
        The datetime index of the EnergySystem

    counter : :obj:`int`
        A counter for rolling horizon optimization windows (iterations)

    timeslice_length_wo_overlap_in_timesteps : :obj:`int`
        The timeslice length without the overlap (in timesteps)

    timeslice_length_with_overlap : :obj:`int`
        The timeslice length with the overlap (in timesteps)

    results : :obj:`pd.DataFrame`
        A DataFrame to store the overall results by concatenating
        the sliced results for each iteration

    power_prices : :obj:`pd.DataFrame`
        A DataFrame to store the power price results

    overall_objective : :obj:`float`
        The overall objective value
        
    overall_solution_time : :obj:`float`
        The overall solution time
    
    solver : :obj:`str`
        The solver to be used (defaults to 'gurobi')
    
    Returns
    -------
    om : :class:`oemof.solph.models.Model`
        The mathematical optimisation model to be solved

    results : :obj:`pd.DataFrame`
        A DataFrame to store the overall results by concatenating
        the sliced results for each iteration

    model_results : :obj:`pd.DataFrame`
        A DataFrame with the results of the particular iteration

    power_prices : :obj:`pd.DataFrame`
        A DataFrame to store the power price results

    overall_objective : :obj:`float`
        The overall objective value
        
    overall_solution_time :obj:`float`
        The overall solution time
    
    """

    om.receive_duals()
    logging.info('Obtaining dual values and reduced costs from the model \n'
                 'in order to calculate power prices.')

    om.solve(solver=solver, solve_kwargs={'tee': True})
    print("********************************************************")
    logging.info("Model run %s done!" % (str(counter)))

    model_results = processing.results(om)
    electricity_bus = views.node(model_results, 'DE_bus_el')
    df_rcut = pd.DataFrame(
        data=electricity_bus['sequences'][
             0:timeslice_length_wo_overlap_in_timesteps])
    results = results.append(df_rcut)

    meta_results = processing.meta_results(om)
    # Objective is weighted in order to take overlap into account
    overall_objective += (int(meta_results['objective'])
                          * (timeslice_length_wo_overlap_in_timesteps
                             / timeslice_length_with_overlap))
    overall_solution_time += meta_results['solver']['Time']

    pps = get_power_prices_from_duals(
        om, datetime_index).iloc[0:timeslice_length_wo_overlap_in_timesteps]
    power_prices = power_prices.append(pps)

    return (om, model_results, results, overall_objective,
            overall_solution_time, power_prices)


# TODO: Resume here, JK / YW
def reconstruct_objective_value(om):
    """ WORK IN PROGRESS; NO WARRANTY, THERE MAY BE BUGS HERE! """
    variable_costs = 0
    gradient_costs = 0

    for i, o in om.FLOWS:
        if om.flows[i, o].variable_costs[0] is not None:
            for t in om.TIMESTEPS:
                variable_costs += (
                            om.flow[i, o, t] * om.objective_weighting[t] *
                            om.flows[i, o].variable_costs[t])

        if om.flows[i, o].positive_gradient['ub'][0] is not None:
            for t in om.TIMESTEPS:
                gradient_costs += (om.flows[i, o].positive_gradient[i, o, t] *
                                   om.flows[i, o].positive_gradient[
                                       'costs'])

        if om.flows[i, o].negative_gradient['ub'][0] is not None:
            for t in om.TIMESTEPS:
                gradient_costs += (om.flows[i, o].negative_gradient[i, o, t] *
                                   om.flows[i, o].negative_gradient[
                                       'costs'])

    return variable_costs + gradient_costs


def dump_es(om, es, path, timestamp):
    """Create a dump of the energy system """

    es.results['main'] = processing.results(om)
    es.results['meta'] = processing.meta_results(om)

    filename = "es_dump_" + timestamp + ".oemof"

    es.dump(dpath=path, filename=filename)

    return None
