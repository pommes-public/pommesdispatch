# -*- coding: utf-8 -*-
"""
General description
------------------
This file contains all subroutines used for reading in input data
for the dispatch variant of POMMES.

Functions build_XX_transformer represent a hierarchical structure:
    build_XX_transformer builds a single transformer element of a given type
    and returns this to create_XX_transformers as node_dict[i], so the i_th
    element to be build

@author: Johannes Kochems (*), Yannick Werner (*), Johannes Giehl,
Benjamin Grosse

Contributors:
Sophie Westphal, Flora von Mikulicz-Radecki, Carla Spiller, Fabian Büllesbach,
Timona Ghosh, Paul Verwiebe, Leticia Encinas Rosa, Joachim Müller-Kirchenbauer

(*) Corresponding authors
"""
import math

import numpy as np
import pandas as pd

import oemof.solph as solph


def load_input_data(filename=None,
                    path_folder_input='../data/Outputlisten/',
                    countries=None,
                    reindex=False):
    r"""Load input data from csv files.

    Parameters
    ----------
    filename : :obj:`str`
        Name of .csv file containing data

    path_folder_input : :obj:`str`
        The path_folder_output where the input data is stored

    countries : :obj:`list` of str
        List of countries to be simulated

    reindex : boolean
        If reindex is True, the given year will be used for reindexing

    year : str
        The year to be used for reindexing

    Returns
    -------
    df :pandas:`pandas.DataFrame`
        DataFrame containing information about nodes or time series.
    """
    df = pd.read_csv(path_folder_input + filename + '.csv', index_col=0)

    if 'country' in df.columns and countries is not None:
        df = df[df['country'].isin(countries)]

    # TODO: Tidy this up and make it robust
    if (('_ts' in filename
         or 'market_values' in filename
         or 'min_loads' in filename)
            and reindex is True):
        df.index = pd.DatetimeIndex(df.index)
        df.index.freq = 'H'
        datediff = (df.index[0]
                    - pd.Timestamp("2017-01-01 00:00:00",
                                   tz=df.index.tz))
        ts_start = (pd.Timestamp("2030-01-01 00:00:00",
                                 tz=df.index.tz)
                    + datediff)
        # account for leap years
        if ts_start.month == 12:
            ts_start = ts_start + pd.Timedelta("1 days")
        new_index = pd.date_range(start=ts_start,
                                  periods=df.shape[0],
                                  freq=df.index.freq)
        df.index = new_index

    if df.isna().any().any() and '_ts' in filename:
        print(
            f'Attention! Time series input data file '
            f'{filename} contains NaNs.'
        )
        print(df.loc[df.isna().any(axis=1)])

    return df


def create_buses(buses_df, node_dict):
    r"""Create buses and add them to the dict of nodes.
    
    Parameters
    ----------
    buses_df : :obj:`pd.DataFrame`
        pd.DataFrame containing the bus elements to be created

    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Dictionary containing all nodes of the EnergySystem

    Returns
    -------
    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Modified dictionary containing all nodes of the EnergySystem including
        the buses elements
    """
    for i, b in buses_df.iterrows():
        node_dict[i] = solph.Bus(label=i)

    return node_dict


# TODO: Update to changed link definition from solph v0.4.2: 2 inputs & outputs
def create_links(links_df, links_capacities_actual_df,
                 node_dict, starttime, endtime, year):
    r"""Create links and add them to the dict of nodes.
    
    Parameters
    ----------
    links_df : :obj:`pd.DataFrame`
        pd.DataFrame containing the link elements to be created
        
    links_capacities_actual_df : :obj:`pd.DataFrame`
        pd.DataFrame containing the link elements to be created    

    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Dictionary containing all nodes of the EnergySystem
        
    starttime : :obj:`str`
        The starting timestamp of the optimization timeframe
   
    endtime : :obj:`str`
        The end timestamp of the optimization timeframe
        
    year: :obj:`str`
        Reference year for pathways depending on starttime (and endtime)  
    
    Returns
    -------
    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Modified dictionary containing all nodes of the EnergySystem including
        the link elements
    """
    # try and except statement since not all countries might be modeled
    for i, l in links_df.iterrows():
        try:
            if l['type'] == 'DC':
                node_dict[i] = solph.custom.Link(
                    label=i,
                    inputs={node_dict[l['from']]:
                                solph.Flow(nominal_value=l[year])},
                    outputs={node_dict[l['to']]:
                                 solph.Flow()},
                    conversion_factors={
                        (node_dict[l['from']], node_dict[l['to']]):
                            l['conversion_factor']}
                )

            if l['type'] == 'AC':
                node_dict[i] = solph.custom.Link(
                    label=i,
                    inputs={node_dict[l['from']]:
                                solph.Flow(nominal_value=l[year],
                                           max=links_capacities_actual_df[i][
                                               starttime:endtime].to_numpy())},
                    outputs={node_dict[l['to']]:
                                 solph.Flow()},
                    conversion_factors={
                        (node_dict[l['from']], node_dict[l['to']]):
                            l['conversion_factor']}
                )

        except KeyError:
            pass

    return node_dict


def create_commodity_sources(commodity_sources_df=None,
                             fuel_costs_df=None,
                             carbon_costs_df=None,
                             node_dict=None,
                             year=2017):
    r"""Create commodity sources and add them to the dict of nodes.
    
    Parameters
    ----------
    commodity_sources_df : :obj:`pd.DataFrame`
        pd.DataFrame containing the commodity source elements to be created, 
        including the corresponding emission factors and carbon prices 

    fuel_costs_df : :obj:`pd.DataFrame`
        pd.DataFrame containing the fuel costs data

    carbon_costs_df : :pandas:`pandas.DataFrame`
        Carbon costs for each commodity source

    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Dictionary containing all nodes of the EnergySystem
        
    year: :obj:`str`
        Reference year for pathways depending on starttime (and endtime)     

    Returns
    -------
    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Modified dictionary containing all nodes of the EnergySystem including 
        the commodity source elements
    """
    if fuel_costs_df is not None and carbon_costs_df is not None:
        for i, cs in commodity_sources_df.iterrows():
            node_dict[i] = solph.Source(
                label=i,
                outputs={node_dict[cs['to']]: solph.Flow(
                    variable_costs=(fuel_costs_df.loc[i, year]
                                    + carbon_costs_df.loc[i, year]
                                    * cs['emission_factors']),
                    emission_factor=cs['emission_factors'])})
    # Fluctuating renewables in Germany
    else:
        for i, cs in commodity_sources_df.iterrows():
            node_dict[i] = solph.Source(
                label=i,
                outputs={node_dict[cs['to']]:
                             solph.Flow()})

    return node_dict


# TODO: Show a warning if shortage or excess is active
def create_shortage_sources(shortage_df, node_dict):
    r"""Create shortage sources and add them to the dict of nodes.
    
    Parameters
    ----------
    shortage_df : :obj:`pd.DataFrame`
        pd.DataFrame containing the shortage source elements to be created
    
    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Dictionary containing all nodes of the EnergySystem  

    Returns
    -------
    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Modified dictionary containing all nodes of the EnergySystem including
        the shortage source elements 
    """

    for i, s in shortage_df.iterrows():
        node_dict[i] = solph.Source(
            label=i,
            outputs={node_dict[s['to']]: solph.Flow(
                variable_costs=s['shortage_costs'])})

    return node_dict


def create_renewables(renewables_df, timeseries_df,
                      starttime, endtime, node_dict):
    r"""Create renewable sources and add them to the dict of nodes.
    
    Parameters
    ----------
    renewables_df : :obj:`pd.DataFrame`
        pd.DataFrame containing the renewables source elements to be created
    
    timeseries_df : :obj:`pd.DataFrame`
        pd.DataFrame containing the timeseries data
        
    starttime : :obj:`str`
        The starting timestamp of the optimization timeframe
   
    endtime : :obj:`str`
        The end timestamp of the optimization timeframe        

    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Dictionary containing all nodes of the EnergySystem     

    Returns
    -------
    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Modified dictionary containing all nodes of the EnergySystem
        including the renewables source elements
        
    """

    for i, re in renewables_df.iterrows():
        try:
            node_dict[i] = solph.Source(
                label=i,
                outputs={node_dict[re['to']]: solph.Flow(
                    fix=np.array(timeseries_df[i][starttime:endtime]),
                    nominal_value=re['capacity'])})
        except KeyError:
            print(re)

    return node_dict


def create_demand(demand_df, timeseries_df,
                  starttime, endtime, node_dict,
                  ActivateDemandResponse=False,
                  dr_overall_load_ts_df=None):
    r"""Create demand sinks and add them to the dict of nodes.
    
    Parameters
    ----------
    demand_df : :obj:`pd.DataFrame`
        pd.DataFrame containing the demand sink elements to be created
    
    timeseries_df : :obj:`pd.DataFrame`
        pd.DataFrame containing the timeseries data

    starttime : :obj:`str`
        The starting timestamp of the optimization timeframe
   
    endtime : :obj:`str`
        The end timestamp of the optimization timeframe        

    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Dictionary containing all nodes of the EnergySystem

    ActivateDemandResponse : :obj:`boolean`
        Boolean control parameter indicating whether or not to introduce
        demand response units

    dr_overall_load_ts_df : :pandas:`pandas.Series`
        The overall load time series from demand response units which is
        used to decrement overall electrical load for Germany
        NOTE: This shall be substituted through a version which already
        includes this in the data preparation

    Returns
    -------
    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Modified dictionary containing all nodes of the EnergySystem
        including the demand sink elements
    
    """

    for i, d in demand_df.iterrows():
        kwargs_dict = {
            'label': i,
            'inputs': {node_dict[d['from']]: solph.Flow(
                fix=np.array(timeseries_df[i][starttime:endtime]),
                nominal_value=d['maximum'])}}

        # TODO: Include into data preparation and write adjusted demand
        # Adjusted demand here means the difference between overall demand
        # and default load profile for demand response units
        if ActivateDemandResponse:
            if i == 'DE_sink_el_load':
                kwargs_dict['inputs'] = {node_dict[d['from']]: solph.Flow(
                    fix=np.array(timeseries_df[i][starttime:endtime]
                        .mul(d['maximum'])
                        .sub(
                        dr_overall_load_ts_df[starttime:endtime])),
                    nominal_value=1)}

        node_dict[i] = solph.Sink(**kwargs_dict)

    return node_dict


# TODO: Resume and include modeling approaches into project
def create_demand_response_units(demand_response_df, load_timeseries_df,
                                 availability_timeseries_pos_df,
                                 availability_timeseries_neg_df,
                                 approach, starttime, endtime,
                                 node_dict):
    r"""Create demand response units and add them to the dict of nodes.

    The demand response modeling approach can be chosen from different
    approaches that have been implemented.

    Parameters
    ----------
    demand_response_df : :pandas:`pandas.DataFrame`
        pd.DataFrame containing the demand response sink elements to be created

    load_timeseries_df : :pandas:`pandas.DataFrame`
        pd.DataFrame containing the load timeseries for the demand response
        clusters to be modeled

    availability_timeseries_pos_df : :pandas:`pandas.DataFrame`
        pd.DataFrame containing the availability timeseries for the demand
        response clusters for downwards shifts (positive direction)

    availability_timeseries_neg_df : :pandas:`pandas.DataFrame`
        pd.DataFrame containing the availability timeseries for the demand
        response clusters for upwards shifts (negative direction)

    approach : :obj:`str`
        Demand response modeling approach to be used;
        must be one of ['DIW', 'DLR', 'IER', 'TUD']

    starttime : :obj:`str`
        The starting timestamp of the optimization timeframe

    endtime : :obj:`str`
        The end timestamp of the optimization timeframe

    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Dictionary containing all nodes of the EnergySystem

    Returns
    -------
    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Modified dictionary containing all nodes of the EnergySystem including
        the demand response sink elements

    dr_overall_load_ts : :pandas:`pandas.Series`
        The overall load time series from demand response units which is
        used to decrement overall electrical load for Germany
        NOTE: This shall be substituted through a version which already
        includes this in the data preparation
    """

    for i, d in demand_response_df.iterrows():
        # Use kwargs dict for easier assignment of parameters
        # kwargs for all DR modeling approaches
        kwargs_all = {
            'demand': np.array(load_timeseries_df[i].loc[starttime:endtime]),
            'max_demand': d['max_cap'],
            'capacity_up': np.array(availability_timeseries_neg_df[i]
                                    .loc[starttime:endtime]),
            'max_capacity_up': d['potential_neg_overall'],
            'capacity_down': np.array(availability_timeseries_pos_df[i]
                                      .loc[starttime:endtime]),
            'max_capacity_down': d['potential_pos_overall'],
            'delay_time': math.ceil(d['shifting_duration']),
            'shed_time': 1,
            'recovery_time_shift': math.ceil(d['regeneration_duration']),
            'recovery_time_shed': 0,
            'cost_dsm_up': d['variable_costs'] / 2,
            'cost_dsm_down_shift': d['variable_costs'] / 2,
            'cost_dsm_down_shed': 10000,
            'efficiency': 1,
            'shed_eligibility': False,
            'shift_eligibility': True,
        }

        # kwargs dependent on DR modeling approach chosen
        kwargs_dict = {
            'DIW': {'method': 'delay',
                    'shift_interval': 24},

            'DLR': {'shift_time': d['interference_duration_pos'],
                    'ActivateYearLimit': True,
                    'ActivateDayLimit': False,
                    'n_yearLimit_shift': np.max(
                        [round(d['maximum_activations_year']), 1]),
                    'n_yearLimit_shed': 1,
                    't_dayLimit': 24,
                    'addition': False,
                    'fixes': True},

            'oemof': {}
        }

        approach_dict = {
            "DLR": solph.custom.SinkDSM(
                label=i,
                inputs={node_dict[d['from']]: solph.Flow(variable_costs=0)},
                **kwargs_all,
                **kwargs_dict["DLR"]),
            "DIW": solph.custom.SinkDSM(
                label=i,
                inputs={node_dict[d['from']]: solph.Flow(variable_costs=0)},
                **kwargs_all,
                **kwargs_dict["DIW"]),
            "oemof": solph.custom.SinkDSM(
                label=i,
                inputs={node_dict[d['from']]: solph.Flow(variable_costs=0)},
                **kwargs_all,
                **kwargs_dict["oemof"]),
        }

        node_dict[i] = approach_dict[approach]

    # Calculate overall electrical load from demand response units
    dr_overall_load_ts_df = load_timeseries_df.mul(
        demand_response_df['max_cap']).sum(axis=1)

    return node_dict, dr_overall_load_ts_df


def create_excess_sinks(excess_df, node_dict):
    """Create excess sinks and add them to the dict of nodes.

    The German excess sink is additionally connected to the renewable buses
    including punishment costs, which is needed to model negative prices.
    It is therefore excluded in the DataFrame that is read in.
    
    Parameters
    ----------
    excess_df : :obj:`pd.DataFrame`
        pd.DataFrame containing the excess sink elements to be created
    
    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Dictionary containing all nodes of the EnergySystem  

    Returns
    -------
    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Modified dictionary containing all nodes of the EnergySystem including 
        the excess sink elements 
    """
    for i, e in excess_df.iterrows():
        node_dict[i] = solph.Sink(
            label=i,
            inputs={node_dict[e['from']]: solph.Flow(variable_costs=1000)})

    # The German sink is special due to a different input
    try:
        node_dict['DE_sink_el_excess'] = solph.Sink(
            label='DE_sink_el_excess',
            inputs={node_dict['DE_bus_windoffshore']:
                        solph.Flow(variable_costs=0),
                    node_dict['DE_bus_windonshore']:
                        solph.Flow(variable_costs=0),
                    node_dict['DE_bus_solarPV']:
                        solph.Flow(variable_costs=0)})
    except KeyError:
        pass

    return node_dict


def build_chp_transformer(i, t, node_dict, outflow_args_el, outflow_args_th):
    """Build a CHP transformer (fixed relation heat / power)
    
    Parameters
    ----------
    i : :obj:`str`
        label of current transformer (within iteration)
    
    t : :obj:`pd.Series`
        pd.Series containing attributes for transformer component
        (row-wise data entries)

    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Dictionary containing all nodes of the EnergySystem     
    
    outflow_args_el: :obj:`dict`
        Dictionary holding the values for electrical outflow arguments
    
    outflow_args_th: :obj:`dict`
        Dictionary holding the values for thermal outflow arguments

    Returns
    -------
    node_dict[i] : `transformer <oemof.network.Transformer>`
        The transformer element to be added to the dict of nodes
        as i-th element
    
    """

    node_dict[i] = solph.Transformer(
        label=i,
        inputs={node_dict[t['from']]: solph.Flow()},
        outputs={
            node_dict[t['to_el']]: solph.Flow(**outflow_args_el),
            node_dict[t['to_th']]: solph.Flow(**outflow_args_th)},
        conversion_factors={
            node_dict[t['to_el']]: t['efficiency_el_CC'],
            node_dict[t['to_th']]: t['efficiency_th_CC']})

    return node_dict[i]


def build_var_chp_transformer(i, t, node_dict, outflow_args_el,
                              outflow_args_th):
    """Build variable CHP transformer.

    (fixed relation heat / power or condensing only)
    
    Parameters
    ----------
    i : :obj:`str`
        label of current transformer (within iteration)
    
    t : :obj:`pd.Series`
        pd.Series containing attributes for transformer component
        (row-wise data entries)

    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Dictionary containing all nodes of the EnergySystem     
    
    outflow_args_el: :obj:`dict`
        Dictionary holding the values for electrical outflow arguments
    
    outflow_args_th: :obj:`dict`
        Dictionary holding the values for thermal outflow arguments

    Returns
    -------
    node_dict[i] : `transformer <oemof.network.Transformer>`
        The transformer element to be added to the dict of nodes
        as i-th element
    
    """

    node_dict[i] = solph.Transformer(
        label=i,
        inputs={node_dict[t['from']]: solph.Flow()},
        outputs={
            node_dict[t['to_el']]: solph.Flow(**outflow_args_el),
            node_dict[t['to_th']]: solph.Flow(**outflow_args_th)},
        conversion_factors={
            node_dict[t['to_el']]: t['efficiency_el_CC'],
            node_dict[t['to_th']]: t['efficiency_th_CC']},
        conversion_factor_full_condensation={
            node_dict[t['to_el']]: t['efficiency_el']})

    return node_dict[i]


def build_condensing_transformer(i, t, node_dict, outflow_args_el):
    """Build a regular condensing transformer
    
    Parameters
    ----------
    i : :obj:`str`
        label of current transformer (within iteration)
    
    t : :obj:`pd.Series`
        pd.Series containing attributes for transformer component
        (row-wise data entries)

    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Dictionary containing all nodes of the EnergySystem     
    
    outflow_args_el: :obj:`dict`
        Dictionary holding the values for electrical outflow arguments

    Returns
    -------
    node_dict[i] : `transformer <oemof.network.Transformer>`
        The transformer element to be added to the dict of nodes
        as i-th element
    
    """

    node_dict[i] = solph.Transformer(
        label=i,
        inputs={node_dict[t['from']]: solph.Flow()},
        outputs={node_dict[t['to_el']]: solph.Flow(**outflow_args_el)},
        conversion_factors={node_dict[t['to_el']]: t['efficiency_el']})

    return node_dict[i]


def create_transformers_conventional(transformers_df,
                                     starttime,
                                     endtime,
                                     node_dict,
                                     operation_costs_df,
                                     # fixed_costs_df,
                                     ramping_costs_df,
                                     transformer_min_load_df,
                                     min_loads_dh,
                                     min_loads_ipp,
                                     year=2017):
    """Create transformers elements and add them to the dict of nodes
    
    Parameters
    ----------
    transformers_df : :obj:`pd.DataFrame`
        pd.DataFrame containing the transformer elements to be created

    starttime : :obj:`str`
        The starting timestamp of the optimization timeframe

    endtime : :obj:`str`
        The end timestamp of the optimization timeframe

    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Dictionary containing all nodes of the EnergySystem     
    
    operation_costs_df : :obj:`pd.DataFrame`
        pd.DataFrame containing the operation costs for all transformers
        
    ramping_costs_df : :obj:`pd.DataFrame`
        pd.DataFrame containing the ramping costs for all transformers

    transformer_min_load_df: :obj:`pd.DataFrame`
        Minimum load timeseries DataFrame for transformer units

    min_loads_dh: :obj:`pd.DataFrame`
        Minimum load timeseries DataFrame for transformer units
        supplying district heating networks

    min_loads_ipp: :obj:`pd.DataFrame`
        Minimum load timeseries DataFrame for transformer units
        serving as industrial power plants

    year: :obj:`str`
        Reference year for pathways depending on starttime

    Returns
    -------
    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Modified dictionary containing all nodes of the EnergySystem
        including the demand sink elements
        
    """

    for i, t in transformers_df.iterrows():

        outflow_args_el = {
            'nominal_value': t['capacity'],
            'variable_costs': operation_costs_df.loc[t['from'], year],
            # fixed_costs_df.loc[starttime:endtime, t['fuel']].to_numpy(),
            'min': t['min_load_factor'],
            'max': t['max_load_factor'],

            'positive_gradient': {
                'ub': t['grad_pos'],
                'costs': ramping_costs_df.loc[t['from'], year]},
            'negative_gradient': {
                'ub': t['grad_neg'],
                'costs': ramping_costs_df.loc[t['from'], year]}
        }

        if t['country'] == 'DE':
            if t['type'] == 'chp':
                if t['identifier'] in min_loads_dh.columns:
                    outflow_args_el['min'] = (
                        min_loads_dh.loc[starttime:endtime,
                        t['identifier']].to_numpy())
                elif t['fuel'] in ['natgas', 'hardcoal', 'lignite']:
                    outflow_args_el['min'] = (
                        transformer_min_load_df.loc[starttime:endtime,
                        'chp_' + t['fuel']].to_numpy())
                else:
                    outflow_args_el['min'] = (
                        transformer_min_load_df.loc[starttime:endtime,
                        'chp'].to_numpy())

            if t['type'] == 'ipp':
                if t['identifier'] in min_loads_ipp.columns:
                    outflow_args_el['min'] = (
                        min_loads_ipp.loc[starttime:endtime,
                        t['identifier']].to_numpy())
                else:
                    outflow_args_el['min'] = (
                        transformer_min_load_df.loc[starttime:endtime,
                        'ipp'].to_numpy())

        if t['country'] in ['AT', 'FR'] and t['country'] == 'natgas':
            outflow_args_el['min'] = (
                transformer_min_load_df.loc[starttime:endtime,
                t['country'] + '_natgas'].to_numpy())
            outflow_args_el['max'] = (
                    transformer_min_load_df.loc[starttime:endtime,
                    t['country'] + '_natgas'].to_numpy() + 0.01)

        node_dict[i] = build_condensing_transformer(
            i, t, node_dict, outflow_args_el)

    return node_dict


def create_transformers_RES(transformers_renewables,
                            sources_renewables_ts,
                            costs_operation_renewables,
                            costs_ramping,
                            costs_market_values,
                            starttime,
                            endtime,
                            node_dict,
                            year=2017):
    """Create renewable energy transformers and add them to the dict of nodes.

    Parameters
    ----------
    transformers_renewables: :obj:`pd.DataFrame`
        pd.DataFrame containing clusters of renewable energy power plants

    sources_renewables_ts: :obj:`pd.DataFrame`
        pd.DataFrame containing renewable profiles

    costs_operation_renewables: :obj:`pd.DataFrame`
        pd.DataFrame containing the operation costs for all transformers
        (negative values applied)

    costs_ramping: :obj:`pd.DataFrame`
        pd.DataFrame containing the ramping costs for all transformers

    costs_market_values: :obj:`pd.DataFrame`
        pd.DataFrame containing technology specfic markte values of renewables

    starttime: :obj:`str`
        The starting timestamp of the optimization timeframe

    endtime: :obj:`str`
        The end timestamp of the optimization timeframe

    node_dict: :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Dictionary containing all nodes of the EnergySystem

    year: :obj:`str`
        Reference year for pathways depending on starttime

    Returns
    -------
    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Modified dictionary containing all nodes of the EnergySystem
        including the renewable transformer elements
    """

    for i, t in transformers_renewables.iterrows():
        # endogeneous fRES
        if not t['fixed']:
            outflow_args_el = {
                'nominal_value': t['capacity'],
                'variable_costs': (
                        costs_operation_renewables.at[i, 'costs']
                        + np.array(costs_market_values[t['from']][starttime:
                                                                  endtime])),
                'min': t['min_load_factor'],
                'max': np.array(sources_renewables_ts[t['from']][starttime:
                                                                 endtime]),
                'positive_gradient': {
                    'ub': t['grad_pos'],
                    'costs': costs_ramping.loc[t['from'], year]},
                'negative_gradient': {
                    'ub': t['grad_neg'],
                    'costs': costs_ramping.loc[t['from'], year]}
            }

            node_dict[i] = solph.Transformer(
                label=i,
                inputs={node_dict[t['from']]: solph.Flow()},
                outputs={node_dict[t['to_el']]:
                             solph.Flow(**outflow_args_el)},
                conversion_factors={node_dict[t['to_el']]:
                                        t['efficiency_el']})

        # exogeneous fRES
        else:
            node_dict[i] = solph.Transformer(
                label=i,
                inputs={node_dict[t['from']]:
                            solph.Flow()},
                outputs={node_dict[t['to_el']]:
                    solph.Flow(
                        nominal_value=t['capacity'],
                        fix=np.array(
                            sources_renewables_ts[t['from']][starttime:
                                                             endtime]))},
                conversion_factors={node_dict[t['to_el']]:
                                        t['efficiency_el']})

    return node_dict


def create_storages(storages_df, storage_var_costs_df,
                    node_dict, year=2017):
    """ Create storages and add the to the dict of nodes.
    
    Parameters
    ----------   
    storages_df : :obj:`pd.DataFrame`
        pd.DataFrame containing the storages elements to be created
    
    storage_var_costs_df : :obj:`pd.DataFrame`
        pd.DataFrame containing the storages variable costs data
    
    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Dictionary containing all nodes of the EnergySystem     
    
    year: :obj:`str`
        Reference year for pathways depending on starttime
        
    Returns
    -------
    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Modified dictionary containing all nodes of the EnergySystem
        including the storage elements
        
    """

    for i, s in storages_df.iterrows():

        if s['type'] == 'phes':
            node_dict[i] = solph.components.GenericStorage(
                label=i,
                inputs={node_dict[s['bus_inflow']]: solph.Flow(
                    nominal_value=s['capacity_pump'],
                    variable_costs=storage_var_costs_df.loc[i, year])},
                outputs={node_dict[s['bus_outflow']]: solph.Flow(
                    nominal_value=s['capacity_turbine'],
                    variable_costs=storage_var_costs_df.loc[i, year])},
                nominal_storage_capacity=s['nominal_storable_energy'],
                loss_rate=s['loss_rate'],
                initial_storage_level=s['initial_storage_level'],
                max_storage_level=s['max_storage_level'],
                min_storage_level=s['min_storage_level'],
                inflow_conversion_factor=s['efficiency_pump'],
                outflow_conversion_factor=s['efficiency_turbine'],
                balanced=True
            )

        if s['type'] == 'reservoir':
            node_dict[i] = solph.components.GenericStorage(
                label=i,
                inputs={node_dict[s['bus_inflow']]: solph.Flow()},
                outputs={node_dict[s['bus_outflow']]: solph.Flow(
                    nominal_value=s['capacity_turbine'],
                    variable_costs=storage_var_costs_df.loc[i, year],
                    min=s['min_load_factor'],
                    max=s['max_load_factor'])},
                nominal_storage_capacity=s['nominal_storable_energy'],
                loss_rate=s['loss_rate'],
                initial_storage_level=s['initial_storage_level'],
                max_storage_level=s['max_storage_level'],
                min_storage_level=s['min_storage_level'],
                inflow_conversion_factor=s['efficiency_pump'],
                outflow_conversion_factor=s['efficiency_turbine'],
                balanced=True
            )

    return node_dict


def create_storages_rh(storages_df, storage_var_costs_df,
                       storages_init_df, node_dict, year=2017):
    """ Function to read in data from storages table and to create the storages elements
    by adding them to the dictionary of nodes.
    
    Parameters
    ----------
    storages_df : :obj:`pd.DataFrame`
        pd.DataFrame containing the storages elements to be created
    
    storage_var_costs_df : :obj:`pd.DataFrame`
        pd.DataFrame containing the storages variable costs data

    storages_init_df : :obj;`pd.DataFrame`
        pd.DataFrame containing the storage states from previous iterations 

    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Dictionary containing all nodes of the EnergySystem     
    
    year: :obj:`str`
        Reference year for pathways depending on starttime

    Returns
    -------
    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Modified dictionary containing all nodes of the EnergySystem
        including the demand sink elements
    """

    storage_labels = []

    for i, s in storages_df.iterrows():

        storage_labels.append(i)
        try:
            initial_capacity_last = (
                        storages_init_df.loc[i, 'Capacity_Last_Timestep']
                        / s['nominal_storable_energy'])
        except:
            initial_capacity_last = s['initial_storage_level']

        if s['type'] == 'phes':
            node_dict[i] = solph.components.GenericStorage(
                label=i,
                inputs={node_dict[s['bus_inflow']]: solph.Flow(
                    nominal_value=s['capacity_pump'],
                    variable_costs=storage_var_costs_df.loc[i, year])},
                outputs={node_dict[s['bus_outflow']]: solph.Flow(
                    nominal_value=s['capacity_turbine'],
                    variable_costs=storage_var_costs_df.loc[i, year])},
                nominal_storage_capacity=s['nominal_storable_energy'],
                loss_rate=s['loss_rate'],
                initial_storage_level=initial_capacity_last,
                max_storage_level=s['max_storage_level'],
                min_storage_level=s['min_storage_level'],
                inflow_conversion_factor=s['efficiency_pump'],
                outflow_conversion_factor=s['efficiency_turbine'],
                balanced=True
            )

        if s['type'] == 'reservoir':
            node_dict[i] = solph.components.GenericStorage(
                label=i,
                inputs={node_dict[s['bus_inflow']]: solph.Flow()},
                outputs={node_dict[s['bus_outflow']]: solph.Flow(
                    nominal_value=s['capacity_turbine'],
                    variable_costs=storage_var_costs_df.loc[i, year],
                    min=s['min_load_factor'],
                    max=s['max_load_factor'])},
                nominal_storage_capacity=s['nominal_storable_energy'],
                loss_rate=s['loss_rate'],
                initial_storage_level=initial_capacity_last,
                max_storage_level=s['max_storage_level'],
                min_storage_level=s['min_storage_level'],
                inflow_conversion_factor=s['efficiency_pump'],
                outflow_conversion_factor=s['efficiency_turbine'],
                balanced=True
            )

    return node_dict, storage_labels
