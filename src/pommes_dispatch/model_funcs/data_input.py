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

from subroutines import *
# from supplementary.helper_functions_LP import convert_annual_limit


def parse_input_data(path_folder_input,
                     AggregateInput,
                     countries,
                     fuel_cost_pathway='middle',
                     year=str(2017),
                     ActivateDemandResponse=False,
                     scenario='50'):
    """Read in csv files and build oemof components

    Parameters
    ----------
    path_folder_input : :obj:`str`
        The path_folder_output where the input data is stored

    AggregateInput: :obj:`boolean`
        boolean control variable indicating whether to use complete or aggregated
        transformer input data set

    countries : :obj:`list` of str
        List of countries to be simulated

    fuel_cost_pathway:  :obj:`str`
       The chosen pathway for commodity cost scenarios (lower, middle, upper)

    year: :obj:`str`
        Reference year for pathways depending on starttime

    ActivateDemandResponse : :obj:`boolean`
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
    files = {#'buses': 'buses',
             'links': 'links',
             'links_ts': 'links_ts',
             'sinks_excess': 'sinks_excess',
             'sinks_demand_el': 'sinks_demand_el',
             'sinks_demand_el_ts': 'sinks_demand_el_ts',
             'sources_shortage': 'sources_shortage',
             # 'sources_commodity': 'sources_commodity',
             'sources_renewables_fluc': 'sources_renewables_fluc',
             # 'costs_fuel': 'costs_fuel_' + fuel_cost_pathway,
             # 'costs_ramping': 'costs_ramping',
             # # 'costs_fixed',
             # 'costs_carbon': 'costs_carbon',
             'costs_market_values': 'costs_market_values',
             # 'costs_operation': 'costs_operation',
             # 'costs_operation_storages': 'costs_operation_storages',
             'emission_limits': 'emission_limits'
             }

    add_files = {'buses': 'buses',
                 'sources_commodity': 'sources_commodity',
                 'sources_renewables': 'sources_renewables',
                 'sources_renewables_ts': 'sources_renewables_ts',
                 'storages_el': 'storages_el',
                 'transformers': 'transformers',
                 # 'transformers_minload_ts': 'transformers_minload_ts',
                 'transformers_renewables': 'transformers_renewables',
                 # 'min_loads_dh': 'min_loads_dh',
                 # 'min_loads_ipp': 'min_loads_ipp',
                 'costs_fuel': 'costs_fuel_' + fuel_cost_pathway,
                 'costs_ramping': 'costs_ramping',
                 # 'costs_fixed',
                 'costs_carbon': 'costs_carbon',
                 'costs_operation': 'costs_operation',
                 'costs_operation_renewables': 'costs_operation_renewables',
                 'costs_operation_storages': 'costs_operation_storages'}

    other_files = {'transformers_minload_ts': 'transformers_minload_ts',
                   'min_loads_dh': 'min_loads_dh',
                   'min_loads_ipp': 'min_loads_ipp'}

    # Optionally use aggregated transformer data instead
    if AggregateInput:
        add_files['transformers'] = 'transformers_clustered'

    # Addition: demand response units
    if ActivateDemandResponse:
        add_files['sinks_dr_el'] = 'sinks_demand_response_el_' + scenario
        add_files['sinks_dr_el_ts'] = (
                'sinks_demand_response_el_ts_' + scenario)
        add_files['sinks_dr_el_ava_pos_ts'] = (
                'sinks_demand_response_el_ava_pos_ts_' + scenario)
        add_files['sinks_dr_el_ava_neg_ts'] = (
                'sinks_demand_response_el_ava_neg_ts_' + scenario)

    # Use dedicated 2030 data
    if year == str(2030):
        add_files = {k: v + '_2030' for k, v in add_files.items()}

    files = {**files, **add_files, **other_files}

    input_data = {}
    if not year == str(2030):
        input_data = {key: load_input_data(filename=name,
                                           path_folder_input=path_folder_input,
                                           countries=countries)
                      for key, name in files.items()}
    else:
        input_data = {key: load_input_data(filename=name,
                                           path_folder_input=path_folder_input,
                                           countries=countries,
                                           reindex=True,
                                           year=year)
                      for key, name in files.items()}

    return input_data


def add_components(input_data,
                   starttime='2017-01-01 00:00:00',
                   endtime='2017-01-01 23:00:00',
                   year=2017,
                   ActivateDemandResponse=False,
                   approach='DIW'):
    """Add the oemof components to a dictionary of nodes

    Note: Storages are not included here. They have to be defined
    separately since the approaches differ between RH and simple model.

    Parameters
    ----------
    input_data: :obj:`dict` of :class:`pd.DataFrame`
        The input data given as a dict of DataFrames
        with component names as keys

    starttime : :obj:`str`
        The starting timestamp of the optimization timeframe

    endtime : :obj:`str`
        The end timestamp of the optimization timeframe

    year: :obj:`str`
        Reference year for pathways depending on starttime

    ActivateDemandResponse : :obj:`boolean`
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

    ### create oemof components
    # create buses
    node_dict = create_buses(input_data['buses'], node_dict)

    # create links
    node_dict = create_links(input_data['links'],
                             input_data['links_ts'],
                             node_dict,
                             starttime, endtime,
                             year)

    # create sources
    node_dict = create_commodity_sources(input_data['sources_commodity'],
                                         input_data['costs_fuel'],
                                         input_data['costs_carbon'],
                                         node_dict,
                                         year)

    node_dict = create_shortage_sources(input_data['sources_shortage'], node_dict)

    node_dict = create_renewables(input_data['sources_renewables'],
                                  input_data['sources_renewables_ts'],
                                  starttime, endtime,
                                  node_dict)

    # create fluctuating renewable sources for Germany
    node_dict = create_commodity_sources(
        commodity_sources_df=input_data['sources_renewables_fluc'],
        node_dict=node_dict)

    # create sinks
    if ActivateDemandResponse:

        node_dict, dr_overall_load_ts_df = create_demand_response_units(
            input_data['sinks_dr_el'],
            input_data['sinks_dr_el_ts'],
            input_data['sinks_dr_el_ava_pos_ts'],
            input_data['sinks_dr_el_ava_neg_ts'],
            approach,
            starttime, endtime,
            node_dict)

        node_dict = create_demand(
            input_data['sinks_demand_el'],
            input_data['sinks_demand_el_ts'],
            starttime, endtime,
            node_dict,
            ActivateDemandResponse,
            dr_overall_load_ts_df)
    else:
        node_dict = create_demand(
            input_data['sinks_demand_el'],
            input_data['sinks_demand_el_ts'],
            starttime, endtime,
            node_dict)
    node_dict = create_excess_sinks(
        input_data['sinks_excess'], node_dict)

    # create conventional transformers
    node_dict = create_transformers_conventional(
        input_data['transformers'],
        starttime,
        endtime,
        node_dict,
        input_data['costs_operation'],
        # input_data['costs_fixed'],
        input_data['costs_ramping'],
        input_data['transformers_minload_ts'],
        input_data['min_loads_dh'],
        input_data['min_loads_ipp'],
        year)

    # create renewable transformers
    node_dict = create_transformers_RES(
        input_data['transformers_renewables'],
        input_data['sources_renewables_ts'],
        input_data['costs_operation_renewables'],
        input_data['costs_ramping'],
        input_data['costs_market_values'],
        starttime,
        endtime,
        node_dict,
        year)

    return node_dict


def add_limits(input_data,
               emission_pathway,
               starttime='2017-01-01 00:00:00',
               endtime='2017-01-01 23:00:00'):
    """Add further limits to the optimization model (emissions limit for now)

    Parameters
    ----------
    input_data: :obj:`dict` of :class:`pd.DataFrame`
        The input data given as a dict of DataFrames
        with component names as keys

    emission_pathway : str
        The pathway for emissions reduction to be used

    starttime : :obj:`str`
        The starttime of the optimization run

    endtime : :obj:`str`
        The endtime of the optimization run

    Returns
    -------
    emissions_limit : :obj:`float`
        The emissions limit to be used (converted)
    """
    emissions_limit = convert_annual_limit(
        input_data['emission_limits'][emission_pathway],
        starttime, endtime)

    return emissions_limit


def nodes_from_csv(path_folder_input,
                   AggregateInput,
                   countries,
                   fuel_cost_pathway='middle',
                   starttime='2017-01-01 00:00:00',
                   endtime='2017-01-01 23:00:00',
                   year=2017,
                   ActivateEmissionsLimit=False,
                   emission_pathway='100_percent_linear',
                   ActivateDemandResponse=False,
                   approach='DIW',
                   scenario='50'):
    """Build oemof components from input data

    Parameters
    ----------
    path_folder_input : :obj:`str`
        The path_folder_output where the input data is stored

    AggregateInput: :obj:`boolean`
        boolean control variable indicating whether to use complete or aggregated
        transformer input data set

    countries : :obj:`list` of str
        List of countries to be simulated

    fuel_cost_pathway:  :obj:`str`
        The chosen pathway for commodity cost scenarios (lower, middle, upper)

    starttime : :obj:`str`
        The starting timestamp of the optimization timeframe

    endtime : :obj:`str`
        The end timestamp of the optimization timeframe

    year: :obj:`str`
        Reference year for pathways depending on starttime

    ActivateEmissionsLimit : :obj:`boolean`
        If True, an emission limit is introduced

    emission_pathway : str
        The pathway for emissions reduction to be used

    ActivateDemandResponse : :obj:`boolean`
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

    input_data = parse_input_data(
        path_folder_input,
        AggregateInput,
        countries,
        fuel_cost_pathway,
        year,
        ActivateDemandResponse,
        scenario)

    node_dict = add_components(
        input_data,
        starttime,
        endtime,
        year,
        ActivateDemandResponse,
        approach)

    # create storages
    node_dict = create_storages(
        input_data['storages_el'],
        input_data['costs_operation_storages'],
        node_dict, year)

    emissions_limit = None
    if ActivateEmissionsLimit:
        emissions_limit = add_limits(
            input_data,
            emission_pathway,
            starttime, endtime)

    return node_dict, emissions_limit


def nodes_from_csv_rh(path_folder_input,
                      AggregateInput,
                      countries,
                      timeseries_start,
                      timeslice_length_with_overlap,
                      storages_init_df,
                      freq,
                      fuel_cost_pathway='middle',
                      year=2017,
                      ActivateEmissionsLimit=False,
                      emission_pathway='100_percent_linear',
                      ActivateDemandResponse=False,
                      approach='DIW',
                      scenario='50'):
    """Read in csv files and build oemof components (Rolling Horizon run)

    Runs function for regular optimization run and updates storage values

    Parameters
    ----------
    path_folder_input : :obj:`str`
        The path_folder_output where the input data is stored

    AggregateInput: :obj:`boolean`
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
        Reference year for pathways depending on starttime

    ActivateEmissionsLimit : :obj:`boolean`
        If True, an emission limit is introduced

    emission_pathway : str
        The pathway for emissions reduction to be used

    ActivateDemandResponse : :obj:`boolean`
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
        function initial_states_RH form functions_for_model_control_LP)
    """

    freq_used = {'60min': (timeslice_length_with_overlap, 'h'),
                 '15min': (timeslice_length_with_overlap * 15, 'min')}[freq]

    # Determine starttime and endtime
    starttime = timeseries_start.strftime("%Y-%m-%d %H:%M:%S")
    endtime = (timeseries_start
               + pd.to_timedelta(freq_used[0], freq_used[1])).strftime(
        "%Y-%m-%d %H:%M:%S")

    input_data = parse_input_data(
        path_folder_input,
        AggregateInput,
        countries,
        fuel_cost_pathway,
        year,
        ActivateDemandResponse,
        scenario)

    node_dict = add_components(
        input_data,
        starttime,
        endtime,
        year,
        ActivateDemandResponse,
        approach)

    # create storages (Rolling horizon)
    node_dict, storage_labels = create_storages_rh(
        input_data['storages_el'],
        input_data['costs_operation_storages'],
        storages_init_df,
        node_dict, year)

    emissions_limit = None
    if ActivateEmissionsLimit:
        emissions_limit = add_limits(
            input_data,
            emission_pathway,
            starttime, endtime)

    return node_dict, storage_labels, emissions_limit
