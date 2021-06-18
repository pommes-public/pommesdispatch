# -*- coding: utf-8 -*-
"""
General description
------------------
This file contains all function definitions for reading in input data
used for the dispatch variant of POMMES.

@author: Johannes Kochems (*), Yannick Werner (*), Johannes Giehl,
Benjamin Grosse

Contributors:
Sophie Westphal, Flora von Mikulicz-Radecki, Carla Spiller, Fabian Büllesbach,
Timona Ghosh, Paul Verwiebe, Leticia Encinas Rosa, Joachim Müller-Kirchenbauer

(*) Corresponding authors
"""

from .subroutines import *
from pommes_dispatch.model_funcs import helpers


def parse_input_data(dispatch_model):
    r"""Read in csv files as DataFrames and store them in a dict

    Parameters
    ----------
    dispatch_model : :class:`DispatchModel`
        The dispatch model that is considered

    Returns
    -------
    input_data: :obj:`dict` of :class:`pd.DataFrame`
        The input data given as a dict of DataFrames
        with component names as keys
    """
    files = {
        'links': 'links',
        'links_ts': 'links_ts',
        'sinks_excess': 'sinks_excess',
        'sinks_demand_el': 'sinks_demand_el',
        'sinks_demand_el_ts': 'sinks_demand_el_ts',
        'sources_shortage': 'sources_shortage',
        'sources_renewables_fluc': 'sources_renewables_fluc',
        'costs_market_values': 'costs_market_values',
        'emission_limits': 'emission_limits'}

    # TODO: Adjust to be able to choose an arbitrary year between 2017 and 2030
    files_by_year = {
        'buses': 'buses',
        'sources_commodity': 'sources_commodity',
        'sources_renewables': 'sources_renewables',
        'sources_renewables_ts': 'sources_renewables_ts',
        'storages_el': 'storages_el',
        'transformers': 'transformers',
        'transformers_renewables': 'transformers_renewables',
        'costs_fuel':
            'costs_fuel_' + dispatch_model.fuel_cost_pathway,
        'costs_ramping': 'costs_ramping',
        'costs_carbon': 'costs_carbon',
        'costs_operation': 'costs_operation',
        'costs_operation_renewables': 'costs_operation_renewables',
        'costs_operation_storages': 'costs_operation_storages'}

    other_files = {
        'transformers_minload_ts': 'transformers_minload_ts',
        'min_loads_dh': 'min_loads_dh',
        'min_loads_ipp': 'min_loads_ipp'}

    # Optionally use aggregated transformer data instead
    if dispatch_model.aggregate_input:
        files_by_year['transformers'] = 'transformers_clustered'

    # Add demand response units
    if dispatch_model.activate_demand_response:
        files_by_year['sinks_dr_el'] = (
                'sinks_demand_response_el_'
                + dispatch_model.demand_response_scenario)
        files_by_year['sinks_dr_el_ts'] = (
                'sinks_demand_response_el_ts_'
                + dispatch_model.demand_response_scenario)
        files_by_year['sinks_dr_el_ava_pos_ts'] = (
                'sinks_demand_response_el_ava_pos_ts_'
                + dispatch_model.demand_response_scenario)
        files_by_year['sinks_dr_el_ava_neg_ts'] = (
                'sinks_demand_response_el_ava_neg_ts_'
                + dispatch_model.demand_response_scenario)

    # Use dedicated 2030 data
    if dispatch_model.year == str(2030):
        files_by_year = {k: v + '_2030' for k, v in files_by_year.items()}

    files = {**files, **files_by_year, **other_files}

    if not dispatch_model.year == str(2030):
        input_data = {
            key: load_input_data(
                filename=name,
                path_folder_input=dispatch_model.path_folder_input,
                countries=dispatch_model.countries)
            for key, name in files.items()}
    else:
        input_data = {
            key: load_input_data(
                filename=name,
                path_folder_input=dispatch_model.path_folder_input,
                countries=dispatch_model.countries,
                reindex=True,
                year=dispatch_model.year)
            for key, name in files.items()}

    return input_data


def add_components(input_data,
                   dispatch_model):
    r"""Add the oemof components to a dictionary of nodes

    Note: Storages are not included here. They have to be defined
    separately since the approaches differ between RH and simple model.

    Parameters
    ----------
    input_data: :obj:`dict` of :class:`pd.DataFrame`
        The input data given as a dict of DataFrames
        with component names as keys

    dispatch_model : :class:`DispatchModel`
        The dispatch model that is considered

    Returns
    -------
    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Dictionary containing all nodes of the EnergySystem
    """
    node_dict = {}

    node_dict = create_buses(input_data, node_dict)

    node_dict = create_interconnection_transformers(input_data,
                                                    dispatch_model,
                                                    node_dict)

    # Also creates fluctuating RES sources for Germany
    node_dict = create_commodity_sources(input_data,
                                         dispatch_model,
                                         node_dict)

    node_dict = create_shortage_sources(input_data,
                                        node_dict)

    node_dict = create_renewables(input_data,
                                  dispatch_model,
                                  node_dict)

    # create sinks
    if dispatch_model.activate_demand_response:
        node_dict, dr_overall_load_ts_df = create_demand_response_units(
            input_data,
            dispatch_model,
            node_dict)

        node_dict = create_demand(
            input_data,
            dispatch_model,
            node_dict,
            dr_overall_load_ts_df)
    else:
        node_dict = create_demand(
            input_data,
            dispatch_model,
            node_dict)

    node_dict = create_excess_sinks(input_data,
                                    node_dict)

    # create conventional transformers
    node_dict = create_transformers_conventional(
        input_data,
        dispatch_model,
        node_dict)

    # create renewable transformers
    node_dict = create_transformers_res(
        input_data,
        dispatch_model,
        node_dict)

    return node_dict


def add_limits(input_data,
               emission_pathway,
               start_time='2017-01-01 00:00:00',
               end_time='2017-01-01 23:00:00'):
    r"""Add further limits to the optimization model (emissions limit for now)

    Parameters
    ----------
    input_data: :obj:`dict` of :class:`pd.DataFrame`
        The input data given as a dict of DataFrames
        with component names as keys

    emission_pathway : str
        The pathway for emissions reduction to be used

    start_time : :obj:`str`
        The start_time of the optimization run

    end_time : :obj:`str`
        The end_time of the optimization run

    Returns
    -------
    emissions_limit : :obj:`float`
        The emissions limit to be used (converted)
    """
    emissions_limit = helpers.convert_annual_limit(
        input_data['emission_limits'][emission_pathway],
        start_time, end_time)

    return emissions_limit


def nodes_from_csv(dispatch_model):
    r"""Build oemof components from input data

    Parameters
    ----------
    dispatch_model : :class:`DispatchModel`
        The dispatch model that is considered

    Returns
    -------
    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Dictionary containing all nodes of the EnergySystem
    """
    input_data = parse_input_data(dispatch_model)

    node_dict = add_components(
        input_data,
        dispatch_model)

    node_dict = create_storages(
        input_data,
        dispatch_model,
        node_dict)

    emissions_limit = None
    if dispatch_model.activate_emissions_limit:
        emissions_limit = add_limits(
            input_data,
            dispatch_model.emission_pathway,
            dispatch_model.start_time, dispatch_model.end_time)

    return node_dict, emissions_limit


def nodes_from_csv_rh(path_folder_input,
                      aggregate_input,
                      countries,
                      timeseries_start,
                      timeslice_length_with_overlap,
                      storages_init_df,
                      freq,
                      fuel_cost_pathway='middle',
                      year=2017,
                      activate_emissions_limit=False,
                      emission_pathway='100_percent_linear',
                      activate_demand_response=False,
                      approach='DIW',
                      scenario='50'):
    r"""Read in csv files and build oemof components (Rolling Horizon run)

    Runs function for regular optimization run and updates storage values

    Parameters
    ----------
    path_folder_input : :obj:`str`
        The path_folder_output where the input data is stored

    aggregate_input: :obj:`boolean`
        boolean control variable indicating whether to use complete or
        aggregated transformer input data set

    countries : :obj:`list` of str
        List of countries to be simulated

    timeseries_start : :obj:`pd.Timestamp`
        the adjusted starting timestep for used the next iteration

    timeslice_length_with_overlap : :obj:`int`
        The timeslice length with overlap in timesteps (hours)

    storages_init_df : :obj:`pd.DataFrame`
        DataFrame to store initial states of storages

    freq : :obj:`str`
        The frequency of the timeindex

    fuel_cost_pathway:  :obj:`str`
        The chosen pathway for commodity cost scenarios (lower, middle, upper)

    year: :obj:`str`
        Reference year for pathways depending on start_time

    activate_emissions_limit : :obj:`boolean`
        If True, an emission limit is introduced

    emission_pathway : str
        The pathway for emissions reduction to be used

    activate_demand_response : :obj:`boolean`
        If True, demand response input data is read in

    approach : :obj:`str`
        Demand response modeling approach to be used;
        must be one of ['DIW', 'DLR', 'IER', 'TUD']

    scenario : :obj:`str`
        Demand response scenario to be modeled;
        must be one of ['25', '50', '75'] whereby '25' is the lower,
        i.e. rather pessimistic estimate

    Returns
    -------
    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Dictionary containing all nodes of the EnergySystem

    storage_labels : :obj:`list` of :class:`str`
        A list of the labels of all storage elements included in the model
        used for assessing these and assigning initial states (via the
        function initial_states_RH form functions_for_model_control_LP)+

    emissions_limit : int or None
        The overall emissions limit
    """
    freq_used = {'60min': (timeslice_length_with_overlap, 'h'),
                 '15min': (timeslice_length_with_overlap * 15, 'min')}[freq]

    # Determine start time and end time
    start_time = timeseries_start.strftime("%Y-%m-%d %H:%M:%S")
    end_time = (timeseries_start
                + pd.to_timedelta(freq_used[0], freq_used[1])).strftime(
        "%Y-%m-%d %H:%M:%S")

    input_data = parse_input_data(
        path_folder_input,
        aggregate_input,
        countries,
        fuel_cost_pathway,
        year,
        activate_demand_response,
        scenario)

    node_dict = add_components(
        input_data,
        start_time,
        end_time,
        year,
        activate_demand_response,
        approach)

    # create storages (Rolling horizon)
    node_dict, storage_labels = create_storages_rh(
        input_data['storages_el'],
        input_data['costs_operation_storages'],
        storages_init_df,
        node_dict, year)

    emissions_limit = None
    if activate_emissions_limit:
        emissions_limit = add_limits(
            input_data,
            emission_pathway,
            start_time, end_time)

    return node_dict, storage_labels, emissions_limit
