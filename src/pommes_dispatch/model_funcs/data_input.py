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
# TODO: Prepare pommes_supplementary repo to use import
# from pommes_supplementary.helpers import convert_annual_limit


def parse_input_data(dispatch_model):
        # path_folder_input,
        #              aggregate_input,
        #              countries,
        #              fuel_cost_pathway='middle',
        #              year=str(2017),
        #              activate_demand_response=False,
        #              scenario='50'):
    r"""Read in csv files and build oemof components

    Parameters
    ----------
    path_folder_input : :obj:`str`
        The path_folder_output where the input data is stored

    aggregate_input: :obj:`boolean`
        boolean control variable indicating whether to use complete
        or aggregated transformer input data set

    countries : :obj:`list` of str
        List of countries to be simulated

    fuel_cost_pathway:  :obj:`str`
       The chosen pathway for commodity cost scenarios (lower, middle, upper)

    year: :obj:`str`
        Reference year for pathways depending on start_time

    activate_demand_response : :obj:`boolean`
        If True, demand response input data is read in

    scenario : :obj:`str`
        Demand response scenario to be modeled;
        must be one of ['25', '50', '75'] whereby '25' is the lower,
        i.e. rather pessimistic estimate

    Returns
    -------
    input_data: :obj:`dict` of :class:`pd.DataFrame`
        The input data given as a dict of DataFrames
        with component names as keys
    """
    # save the input data in a dict; keys are names and values are DataFrames
    files = {'links': 'links',
             'links_ts': 'links_ts',
             'sinks_excess': 'sinks_excess',
             'sinks_demand_el': 'sinks_demand_el',
             'sinks_demand_el_ts': 'sinks_demand_el_ts',
             'sources_shortage': 'sources_shortage',
             'sources_renewables_fluc': 'sources_renewables_fluc',
             'costs_market_values': 'costs_market_values',
             'emission_limits': 'emission_limits'}

    add_files = {'buses': 'buses',
                 'sources_commodity': 'sources_commodity',
                 'sources_renewables': 'sources_renewables',
                 'sources_renewables_ts': 'sources_renewables_ts',
                 'storages_el': 'storages_el',
                 'transformers': 'transformers',
                 'transformers_renewables': 'transformers_renewables',
                 'costs_fuel': 'costs_fuel_' + dispatch_model.fuel_cost_pathway,
                 'costs_ramping': 'costs_ramping',
                 'costs_carbon': 'costs_carbon',
                 'costs_operation': 'costs_operation',
                 'costs_operation_renewables': 'costs_operation_renewables',
                 'costs_operation_storages': 'costs_operation_storages'}

    other_files = {'transformers_minload_ts': 'transformers_minload_ts',
                   'min_loads_dh': 'min_loads_dh',
                   'min_loads_ipp': 'min_loads_ipp'}

    # Optionally use aggregated transformer data instead
    if dispatch_model.aggregate_input:
        add_files['transformers'] = 'transformers_clustered'

    # Add demand response units
    if dispatch_model.activate_demand_response:
        add_files['sinks_dr_el'] = 'sinks_demand_response_el_' + dispatch_model.scenario
        add_files['sinks_dr_el_ts'] = (
                'sinks_demand_response_el_ts_' + dispatch_model.scenario)
        add_files['sinks_dr_el_ava_pos_ts'] = (
                'sinks_demand_response_el_ava_pos_ts_' + dispatch_model.scenario)
        add_files['sinks_dr_el_ava_neg_ts'] = (
                'sinks_demand_response_el_ava_neg_ts_' + dispatch_model.scenario)

    # Use dedicated 2030 data
    if dispatch_model.year == str(2030):
        add_files = {k: v + '_2030' for k, v in add_files.items()}

    files = {**files, **add_files, **other_files}

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
                   # start_time='2017-01-01 00:00:00',
                   # end_time='2017-01-01 23:00:00',
                   # year=2017,
                   # activate_demand_response=False,
                   # approach='DLR'):
    r"""Add the oemof components to a dictionary of nodes

    Note: Storages are not included here. They have to be defined
    separately since the approaches differ between RH and simple model.

    Parameters
    ----------
    input_data: :obj:`dict` of :class:`pd.DataFrame`
        The input data given as a dict of DataFrames
        with component names as keys

    start_time : :obj:`str`
        The starting timestamp of the optimization timeframe

    end_time : :obj:`str`
        The end timestamp of the optimization timeframe

    year: :obj:`str`
        Reference year for pathways depending on start_time

    activate_demand_response : :obj:`boolean`
        If True, demand response input data is read in

    approach : :obj:`str`
        Demand response modeling approach to be used;
        must be one of ['DIW', 'DLR', 'IER', 'TUD']

    Returns
    -------
    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Dictionary containing all nodes of the EnergySystem
    """
    # data container for oemof components
    node_dict = {}

    # create buses
    node_dict = create_buses(input_data['buses'], node_dict)

    # create links
    node_dict = create_interconnection_transformers(input_data['links'],
                                                    input_data['links_ts'],
                                                    node_dict,
                                                    dispatch_model.start_time, dispatch_model.end_time,
                                                    dispatch_model.year)

    # create sources
    node_dict = create_commodity_sources(input_data['sources_commodity'],
                                         input_data['costs_fuel'],
                                         input_data['costs_carbon'],
                                         node_dict,
                                         dispatch_model.year)

    node_dict = create_shortage_sources(input_data['sources_shortage'],
                                        node_dict)

    node_dict = create_renewables(input_data['sources_renewables'],
                                  input_data['sources_renewables_ts'],
                                  dispatch_model.start_time, dispatch_model.end_time,
                                  node_dict)

    # create fluctuating renewable sources for Germany
    node_dict = create_commodity_sources(
        commodity_sources_df=input_data['sources_renewables_fluc'],
        node_dict=node_dict)

    # create sinks
    if dispatch_model.activate_demand_response:
        node_dict, dr_overall_load_ts_df = create_demand_response_units(
            input_data['sinks_dr_el'],
            input_data['sinks_dr_el_ts'],
            input_data['sinks_dr_el_ava_pos_ts'],
            input_data['sinks_dr_el_ava_neg_ts'],
            dispatch_model.approach,
            dispatch_model.start_time, dispatch_model.end_time,
            node_dict)

        node_dict = create_demand(
            input_data['sinks_demand_el'],
            input_data['sinks_demand_el_ts'],
            dispatch_model.start_time, dispatch_model.end_time,
            node_dict,
            dispatch_model.activate_demand_response,
            dr_overall_load_ts_df)
    else:
        node_dict = create_demand(
            input_data['sinks_demand_el'],
            input_data['sinks_demand_el_ts'],
            dispatch_model.start_time, dispatch_model.end_time,
            node_dict)

    node_dict = create_excess_sinks(
        input_data['sinks_excess'], node_dict)

    # create conventional transformers
    node_dict = create_transformers_conventional(
        input_data['transformers'],
        dispatch_model.start_time,
        dispatch_model.end_time,
        node_dict,
        input_data['costs_operation'],
        input_data['costs_ramping'],
        input_data['transformers_minload_ts'],
        input_data['min_loads_dh'],
        input_data['min_loads_ipp'],
        dispatch_model.year)

    # create renewable transformers
    node_dict = create_transformers_RES(
        input_data['transformers_renewables'],
        input_data['sources_renewables_ts'],
        input_data['costs_operation_renewables'],
        input_data['costs_ramping'],
        input_data['costs_market_values'],
        dispatch_model.start_time,
        dispatch_model.end_time,
        node_dict,
        dispatch_model.year)

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
    emissions_limit = convert_annual_limit(
        input_data['emission_limits'][emission_pathway],
        start_time, end_time)

    return emissions_limit


def nodes_from_csv(dispatch_model):
        # path_folder_input,
        #            aggregate_input,
        #            countries,
        #            fuel_cost_pathway='middle',
        #            start_time='2017-01-01 00:00:00',
        #            end_time='2017-01-01 23:00:00',
        #            year=2017,
        #            activate_emissions_limit=False,
        #            emission_pathway='100_percent_linear',
        #            activate_demand_response=False,
        #            approach='DIW',
        #            scenario='50'):
    r"""Build oemof components from input data

    Parameters
    ----------
    path_folder_input : :obj:`str`
        The path_folder_output where the input data is stored

    aggregate_input: :obj:`boolean`
        boolean control variable indicating whether to use complete
        or aggregated transformer input data set

    countries : :obj:`list` of str
        List of countries to be simulated

    fuel_cost_pathway:  :obj:`str`
        The chosen pathway for commodity cost scenarios (lower, middle, upper)

    start_time : :obj:`str`
        The starting timestamp of the optimization timeframe

    end_time : :obj:`str`
        The end timestamp of the optimization timeframe

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
    """
    input_data = parse_input_data(dispatch_model)
        # path_folder_input,
        # aggregate_input,
        # countries,
        # fuel_cost_pathway,
        # year,
        # activate_demand_response,
        # scenario)

    node_dict = add_components(
        input_data,
        dispatch_model)
        # start_time,
        # end_time,
        # year,
        # activate_demand_response,
        # approach)

    # create storages
    node_dict = create_storages(
        input_data['storages_el'],
        input_data['costs_operation_storages'],
        node_dict, dispatch_model.year)

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
