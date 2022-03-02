# -*- coding: utf-8 -*-
"""
General description
-------------------
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
import oemof.solph as solph
import pandas as pd


def load_input_data(filename=None,
                    path_folder_input='.inputs/',
                    countries=None):
    r"""Load input data from csv files.

    Display some information on NaN values in time series data.

    Parameters
    ----------
    filename : :obj:`str`
        Name of .csv file containing data

    path_folder_input : :obj:`str`
        The path to the folder where the input data is stored

    countries : :obj:`list` of str
        List of countries to be simulated

    Returns
    -------
    df : :class:`pandas.DataFrame`
        DataFrame containing information about nodes or time series.
    """
    df = pd.read_csv(path_folder_input + filename + '.csv', index_col=0)

    if 'country' in df.columns and countries is not None:
        df = df[df['country'].isin(countries)]

    if df.isna().any().any() and '_ts' in filename:
        print(
            f'Attention! Time series input data file '
            f'{filename} contains NaNs.'
        )
        print(df.loc[df.isna().any(axis=1)])

    return df


def create_buses(input_data, node_dict):
    r"""Create buses and add them to the dict of nodes.

    Parameters
    ----------
    input_data: :obj:`dict` of :class:`pd.DataFrame`
        The input data given as a dict of DataFrames
        with component names as keys

    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Dictionary containing all nodes of the EnergySystem

    Returns
    -------
    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Modified dictionary containing all nodes of the EnergySystem including
        the buses elements
    """
    for i, b in input_data["buses"].iterrows():
        node_dict[i] = solph.Bus(label=i)

    return node_dict


def create_linking_transformers(input_data, dispatch_model, node_dict):
    r"""Create linking transformers and add them to the dict of nodes.

    Linking transformers serve for modeling interconnector capacities

    Parameters
    ----------
    input_data: :obj:`dict` of :class:`pd.DataFrame`
        The input data given as a dict of DataFrames
        with component names as keys

    dispatch_model : :class:`DispatchModel`
        The dispatch model that is considered

    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Dictionary containing all nodes of the EnergySystem

    Returns
    -------
    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Modified dictionary containing all nodes of the EnergySystem including
        the interconnection transformers elements
    """
    # try and except statement since not all countries might be modeled
    for i, l in input_data['linking_transformers'].iterrows():
        try:
            if l['type'] == 'DC':
                node_dict[i] = solph.Transformer(
                    label=i,
                    inputs={
                        node_dict[l['from']]:
                            solph.Flow(
                                nominal_value=l[dispatch_model.year])},
                    outputs={node_dict[l['to']]: solph.Flow()},
                    conversion_factors={
                        (node_dict[l['from']], node_dict[l['to']]):
                            l['conversion_factor']}
                )

            if l['type'] == 'AC':
                node_dict[i] = solph.Transformer(
                    label=i,
                    inputs={
                        node_dict[l['from']]:
                            solph.Flow(
                                nominal_value=l[dispatch_model.year],
                                max=input_data['linking_transformers_ts'][i][
                                    dispatch_model.start_time:
                                    dispatch_model.end_time].to_numpy())},
                    outputs={node_dict[l['to']]: solph.Flow()},
                    conversion_factors={
                        (node_dict[l['from']], node_dict[l['to']]):
                            l['conversion_factor']}
                )

        except KeyError:
            pass

    return node_dict


def create_commodity_sources(input_data, dispatch_model, node_dict):
    r"""Create commodity sources and add them to the dict of nodes.

    Parameters
    ----------
    input_data: :obj:`dict` of :class:`pd.DataFrame`
        The input data given as a dict of DataFrames
        with component names as keys

    dispatch_model : :class:`DispatchModel`
        The dispatch model that is considered

    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Dictionary containing all nodes of the EnergySystem

    Returns
    -------
    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Modified dictionary containing all nodes of the EnergySystem including
        the commodity source elements
    """
    # Regular commodity sources
    for i, cs in input_data["sources_commodity"].iterrows():
        node_dict[i] = solph.Source(
            label=i,
            outputs={node_dict[cs["to"]]: solph.Flow(
                variable_costs=(
                        input_data["costs_fuel"].loc[
                            i, dispatch_model.year]
                        + input_data["costs_emissions"].loc[
                            i, dispatch_model.year]
                        * np.array(
                            input_data['costs_emissions_ts']["price"][
                                dispatch_model.start_time:
                                dispatch_model.end_time])
                        * cs["emission_factors"]),
                emission_factor=cs["emission_factors"])})

    # Fluctuating renewables in Germany
    for i, cs in input_data['sources_renewables_fluc'].iterrows():
        node_dict[i] = solph.Source(
            label=i,
            outputs={node_dict[cs["to"]]: solph.Flow()})

    return node_dict


def create_shortage_sources(input_data, node_dict):
    r"""Create shortage sources and add them to the dict of nodes.

    Parameters
    ----------
    input_data: :obj:`dict` of :class:`pd.DataFrame`
        The input data given as a dict of DataFrames
        with component names as keys

    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Dictionary containing all nodes of the EnergySystem

    Returns
    -------
    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Modified dictionary containing all nodes of the EnergySystem including
        the shortage source elements
    """
    for i, s in input_data["sources_shortage"].iterrows():
        node_dict[i] = solph.Source(
            label=i,
            outputs={node_dict[s["to"]]: solph.Flow(
                variable_costs=s["shortage_costs"])})

    return node_dict


def create_renewables(input_data, dispatch_model, node_dict):
    r"""Create renewable sources and add them to the dict of nodes.

    Parameters
    ----------
    input_data: :obj:`dict` of :class:`pd.DataFrame`
        The input data given as a dict of DataFrames
        with component names as keys

    dispatch_model : :class:`DispatchModel`
        The dispatch model that is considered

    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Dictionary containing all nodes of the EnergySystem

    Returns
    -------
    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Modified dictionary containing all nodes of the EnergySystem
        including the renewables source elements
    """
    for i, re in input_data['sources_renewables'].iterrows():
        try:
            node_dict[i] = solph.Source(
                label=i,
                outputs={node_dict[re['to']]: solph.Flow(
                    fix=np.array(
                        input_data['sources_renewables_ts'][i][
                            dispatch_model.start_time:
                            dispatch_model.end_time]),
                    nominal_value=re['capacity'])})
        except KeyError:
            print(re)

    return node_dict


def create_demand(input_data, dispatch_model, node_dict,
                  dr_overall_load_ts_df=None):
    r"""Create demand sinks and add them to the dict of nodes.

    Parameters
    ----------
    input_data: :obj:`dict` of :class:`pd.DataFrame`
        The input data given as a dict of DataFrames
        with component names as keys

    dispatch_model : :class:`DispatchModel`
        The dispatch model that is considered

    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Dictionary containing all nodes of the EnergySystem

    dr_overall_load_ts_df : :class:`pandas.Series`
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
    for i, d in input_data['sinks_demand_el'].iterrows():
        kwargs_dict = {
            'label': i,
            'inputs': {node_dict[d['from']]: solph.Flow(
                fix=np.array(input_data['sinks_demand_el_ts'][i][
                             dispatch_model.start_time:
                             dispatch_model.end_time]),
                nominal_value=d['maximum'])}}

        # Adjusted demand here means the difference between overall demand
        # and the baseline load profile for demand response units
        if dispatch_model.activate_demand_response:
            if i == 'DE_sink_el_load':
                kwargs_dict['inputs'] = {node_dict[d['from']]: solph.Flow(
                    fix=np.array(
                        input_data['sinks_demand_el_ts'][i][
                                 dispatch_model.start_time:
                                 dispatch_model.end_time]
                        .mul(d['maximum'])
                        .sub(
                            dr_overall_load_ts_df[
                                dispatch_model.start_time:
                                dispatch_model.end_time])),
                    nominal_value=1)}

        node_dict[i] = solph.Sink(**kwargs_dict)

    return node_dict


def create_demand_response_units(input_data, dispatch_model, node_dict):
    r"""Create demand response units and add them to the dict of nodes.

    The demand response modeling approach can be chosen from different
    approaches that have been implemented.

    Parameters
    ----------
    input_data: :obj:`dict` of :class:`pd.DataFrame`
        The input data given as a dict of DataFrames
        with component names as keys

    dispatch_model : :class:`DispatchModel`
        The dispatch model that is considered

    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Dictionary containing all nodes of the EnergySystem

    Returns
    -------
    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Modified dictionary containing all nodes of the EnergySystem including
        the demand response sink elements

    dr_overall_load_ts : :class:`pandas.Series`
        The overall baseline load time series from demand response units
        which is used to decrement overall electrical load for Germany
        NOTE: This shall be substituted through a version which already
        includes this in the data preparation
    """
    for i, d in input_data['sinks_dr_el'].iterrows():
        # kwargs for all demand response modeling approaches
        kwargs_all = {
            'demand': np.array(
                input_data['sinks_dr_el_ts'][i]
                .loc[dispatch_model.start_time:dispatch_model.end_time]),
            'max_demand': d['max_cap'],
            'capacity_up': np.array(
                input_data['sinks_dr_el_ava_neg_ts'][i]
                .loc[dispatch_model.start_time:dispatch_model.end_time]),
            'max_capacity_up': d['potential_neg_overall'],
            'capacity_down': np.array(
                input_data['sinks_dr_el_ava_pos_ts'][i]
                .loc[dispatch_model.start_time:dispatch_model.end_time]),
            'max_capacity_down': d['potential_pos_overall'],
            'delay_time': math.ceil(d['shifting_duration']),
            'shed_time': 1,
            'recovery_time_shed': 0,
            'cost_dsm_up': d['variable_costs'] / 2,
            'cost_dsm_down_shift': d['variable_costs'] / 2,
            'cost_dsm_down_shed': 10000,
            'efficiency': 1,
            'shed_eligibility': False,
            'shift_eligibility': True,
        }

        # kwargs dependent on demand response modeling approach chosen
        kwargs_dict = {
            'DIW': {'approach': 'DIW',
                    'recovery_time_shift': math.ceil(
                        d['regeneration_duration'])},

            'DLR': {'approach': 'DLR',
                    'shift_time': d['interference_duration_pos'],
                    'ActivateYearLimit': True,
                    'ActivateDayLimit': False,
                    'n_yearLimit_shift': np.max(
                        [round(d['maximum_activations_year']), 1]),
                    'n_yearLimit_shed': 1,
                    't_dayLimit': 24,
                    'addition': True,
                    'fixes': True},

            'oemof': {'approach': 'oemof',
                      'shift_interval': 24}
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

        node_dict[i] = approach_dict[dispatch_model.demand_response_approach]

    # Calculate overall electrical baseline load from demand response units
    dr_overall_load_ts_df = input_data['sinks_dr_el_ts'].mul(
        input_data['sinks_dr_el']['max_cap']).sum(axis=1)

    return node_dict, dr_overall_load_ts_df


def create_excess_sinks(input_data, node_dict):
    r"""Create excess sinks and add them to the dict of nodes.

    The German excess sink is additionally connected to the renewable buses
    including penalty costs, which is needed to model negative prices.
    It is therefore excluded in the DataFrame that is read in.

    Parameters
    ----------
    input_data: :obj:`dict` of :class:`pd.DataFrame`
        The input data given as a dict of DataFrames
        with component names as keys

    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Dictionary containing all nodes of the EnergySystem

    Returns
    -------
    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Modified dictionary containing all nodes of the EnergySystem including
        the excess sink elements
    """
    for i, e in input_data["sinks_excess"].iterrows():
        node_dict[i] = solph.Sink(
            label=i,
            inputs={
                node_dict[e['from']]: solph.Flow(
                    variable_costs=e['excess_costs'])
            }
        )

    # The German sink is special due to a different input
    try:
        node_dict['DE_sink_el_excess'] = solph.Sink(
            label='DE_sink_el_excess',
            inputs={
                node_dict['DE_bus_windoffshore']:
                    solph.Flow(variable_costs=0),
                node_dict['DE_bus_windonshore']:
                    solph.Flow(variable_costs=0),
                node_dict['DE_bus_solarPV']:
                    solph.Flow(variable_costs=0)})
    except KeyError:
        pass

    return node_dict


def build_chp_transformer(i, t, node_dict, outflow_args_el, outflow_args_th):
    r"""Build a CHP transformer (fixed relation heat / power)

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


def build_var_chp_units(i, t, node_dict, outflow_args_el,
                        outflow_args_th):
    r"""Build variable CHP units

    These are modeled as extraction turbine CHP units and can choose
    between full condensation mode, full coupling mode
    and any allowed state in between.

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
    node_dict[i] : oemof.solph.custom.ExtractionTurbineCHP
        The extraction turbine element to be added to the dict of nodes
        as i-th element
    """
    node_dict[i] = solph.ExtractionTurbineCHP(
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
    r"""Build a regular condensing transformer

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


def create_transformers_conventional(input_data,
                                     dispatch_model,
                                     node_dict):
    r"""Create transformers elements and add them to the dict of nodes

    Parameters
    ----------
    input_data: :obj:`dict` of :class:`pd.DataFrame`
        The input data given as a dict of DataFrames
        with component names as keys

    dispatch_model : :class:`DispatchModel`
        The dispatch model that is considered

    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Dictionary containing all nodes of the EnergySystem

    Returns
    -------
    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Modified dictionary containing all nodes of the EnergySystem
        including the demand sink elements
    """
    for i, t in input_data['transformers'].iterrows():

        outflow_args_el = {
            'nominal_value': t['capacity'],
            'variable_costs': (
                input_data['costs_operation']
                .loc[t['from'], dispatch_model.year]),
            'min': t['min_load_factor'],
            'max': (
                t['max_load_factor']
            ),

            'positive_gradient': {
                'ub': t['grad_pos'],
                'costs': 0
            },
            'negative_gradient': {
                'ub': t['grad_neg'],
                'costs': 0
            }
        }

        # Assign minimum loads for German CHP and IPP plants
        if t['country'] == 'DE':
            if t['type'] == 'chp':
                if t['identifier'] in input_data['min_loads_dh'].columns:
                    outflow_args_el['min'] = (
                        input_data['min_loads_dh'].loc[
                            dispatch_model.start_time:
                            dispatch_model.end_time,
                            t['identifier']].to_numpy())
                elif t['fuel'] in ['natgas', 'hardcoal', 'lignite']:
                    outflow_args_el['min'] = (
                        input_data['transformers_minload_ts'].loc[
                            dispatch_model.start_time:
                            dispatch_model.end_time,
                            'chp_' + t['fuel']].to_numpy())
                else:
                    outflow_args_el['min'] = (
                        input_data['transformers_minload_ts'].loc[
                            dispatch_model.start_time:
                            dispatch_model.end_time,
                            'chp'].to_numpy())

            if t['type'] == 'ipp':
                if t['identifier'] in input_data['min_loads_ipp'].columns:
                    outflow_args_el['min'] = (
                        input_data['min_loads_ipp'].loc[
                            dispatch_model.start_time:
                            dispatch_model.end_time,
                            t['identifier']].to_numpy())
                else:
                    outflow_args_el['min'] = (
                        input_data['transformers_minload_ts'].loc[
                            dispatch_model.start_time:
                            dispatch_model.end_time,
                            'ipp'].to_numpy())

        # Limit flexibility for Austrian and French natgas plants
        if t['country'] in ['AT', 'FR'] and t['fuel'] == 'natgas':
            outflow_args_el['min'] = (
                input_data['transformers_minload_ts'].loc[
                    dispatch_model.start_time:
                    dispatch_model.end_time,
                    t['country'] + '_natgas'].to_numpy())
            outflow_args_el['max'] = (
                np.minimum(
                    [1] * len(
                        input_data['transformers_minload_ts'].loc[
                            dispatch_model.start_time:
                            dispatch_model.end_time
                        ]
                    ),
                    input_data['transformers_minload_ts'].loc[
                        dispatch_model.start_time:
                        dispatch_model.end_time,
                        t['country'] + '_natgas'
                    ].to_numpy() + 0.05
                )
            )

        # Introduce availability and handle minimum loads
        else:
            outflow_args_el['max'] = (
                np.minimum(
                    [1] * len(
                        input_data['transformers_availability_ts'].loc[
                            dispatch_model.start_time:dispatch_model.end_time
                        ]
                    ),
                    np.maximum(
                        outflow_args_el['min'] + 0.05,
                        outflow_args_el['max']
                        * np.array(
                            input_data[
                                'transformers_availability_ts'
                            ]["values"].loc[
                                dispatch_model.start_time
                                :dispatch_model.end_time
                            ]
                        )
                    )
                )
            )

        node_dict[i] = build_condensing_transformer(
            i, t, node_dict, outflow_args_el)

    return node_dict


def create_transformers_res(input_data,
                            dispatch_model,
                            node_dict):
    r"""Create renewable energy transformers and add them to the dict of nodes.

    Parameters
    ----------
    input_data: :obj:`dict` of :class:`pd.DataFrame`
        The input data given as a dict of DataFrames
        with component names as keys

    dispatch_model : :class:`DispatchModel`
        The dispatch model that is considered

    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Dictionary containing all nodes of the EnergySystem

    Returns
    -------
    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Modified dictionary containing all nodes of the EnergySystem
        including the renewable transformer elements
    """
    for i, t in input_data['transformers_renewables'].iterrows():
        # endogeneous fRES
        if not t['fixed']:
            outflow_args_el = {
                'nominal_value': t['capacity'],
                'variable_costs': (
                    input_data['costs_operation_renewables'].at[i, 'costs']
                    + np.array(
                        input_data['costs_market_values'][
                            t['from']][dispatch_model.start_time:
                                       dispatch_model.end_time])),
                'min': t['min_load_factor'],
                'max': np.array(
                    input_data['sources_renewables_ts'][
                        t['from']][dispatch_model.start_time:
                                   dispatch_model.end_time]),
                'positive_gradient': {
                    'ub': t['grad_pos'],
                    'costs': 0
                },
                'negative_gradient': {
                    'ub': t['grad_neg'],
                    'costs': 0
                }
            }

            node_dict[i] = solph.Transformer(
                label=i,
                inputs={node_dict[t['from']]: solph.Flow()},
                outputs={
                    node_dict[t['to_el']]:
                        solph.Flow(**outflow_args_el)},
                conversion_factors={
                    node_dict[t['to_el']]: t['efficiency_el']})

        # exogeneous fRES
        else:
            node_dict[i] = solph.Transformer(
                label=i,
                inputs={node_dict[t['from']]: solph.Flow()},
                outputs={
                    node_dict[t['to_el']]:
                        solph.Flow(
                            nominal_value=t['capacity'],
                            fix=np.array(
                                input_data['sources_renewables_ts'][
                                    t['from']][dispatch_model.start_time:
                                               dispatch_model.end_time]))},
                conversion_factors={node_dict[t['to_el']]: t['efficiency_el']})

    return node_dict


def create_storages(input_data, dispatch_model, node_dict):
    r"""Create storages and add them to the dict of nodes.

    Parameters
    ----------
    input_data: :obj:`dict` of :class:`pd.DataFrame`
        The input data given as a dict of DataFrames
        with component names as keys

    dispatch_model : :class:`DispatchModel`
        The dispatch model that is considered

    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Dictionary containing all nodes of the EnergySystem

    Returns
    -------
    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Modified dictionary containing all nodes of the EnergySystem
        including the storage elements
    """
    for i, s in input_data['storages_el'].iterrows():

        if s['type'] == 'phes':
            node_dict[i] = solph.components.GenericStorage(
                label=i,
                inputs={node_dict[s['bus_inflow']]: solph.Flow(
                    nominal_value=s['capacity_pump'],
                    variable_costs=(
                        input_data['costs_operation_storages']
                        .loc[i, dispatch_model.year]))},
                outputs={node_dict[s['bus_outflow']]: solph.Flow(
                    nominal_value=s['capacity_turbine'],
                    variable_costs=(
                        input_data['costs_operation_storages']
                        .loc[i, dispatch_model.year]))},
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
                    variable_costs=(
                        input_data['costs_operation_storages']
                        .loc[i, dispatch_model.year]),
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


def create_storages_rolling_horizon(input_data, dispatch_model, node_dict,
                                    iteration_results):
    r"""Create storages, add them to the dict of nodes, return storage labels.

    Parameters
    ----------
    input_data: :obj:`dict` of :class:`pd.DataFrame`
        The input data given as a dict of DataFrames
        with component names as keys

    dispatch_model : :class:`DispatchModel`
        The dispatch model that is considered

    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Dictionary containing all nodes of the EnergySystem

    iteration_results : dict
        A dictionary holding the results of the previous rolling horizon
        iteration

    Returns
    -------
    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Modified dictionary containing all nodes of the EnergySystem
        including the demand sink elements

    storage_labels : list
        List of storage labels
    """
    storage_labels = []

    for i, s in input_data['storages_el'].iterrows():

        storage_labels.append(i)
        if not iteration_results["storages_initial"].empty:
            initial_storage_level_last_iteration = (
                iteration_results["storages_initial"]
                .loc[i, "initial_storage_level_last_iteration"]
                / s["nominal_storable_energy"])
        else:
            initial_storage_level_last_iteration = s["initial_storage_level"]

        if s['type'] == 'phes':
            node_dict[i] = solph.components.GenericStorage(
                label=i,
                inputs={node_dict[s['bus_inflow']]: solph.Flow(
                    nominal_value=s['capacity_pump'],
                    variable_costs=(
                        input_data['costs_operation_storages']
                        .loc[i, dispatch_model.year]))},
                outputs={node_dict[s['bus_outflow']]: solph.Flow(
                    nominal_value=s['capacity_turbine'],
                    variable_costs=(
                        input_data['costs_operation_storages']
                        .loc[i, dispatch_model.year]))},
                nominal_storage_capacity=s['nominal_storable_energy'],
                loss_rate=s['loss_rate'],
                initial_storage_level=initial_storage_level_last_iteration,
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
                    variable_costs=(
                        input_data['costs_operation_storages']
                        .loc[i, dispatch_model.year]),
                    min=s['min_load_factor'],
                    max=s['max_load_factor'])},
                nominal_storage_capacity=s['nominal_storable_energy'],
                loss_rate=s['loss_rate'],
                initial_storage_level=initial_storage_level_last_iteration,
                max_storage_level=s['max_storage_level'],
                min_storage_level=s['min_storage_level'],
                inflow_conversion_factor=s['efficiency_pump'],
                outflow_conversion_factor=s['efficiency_turbine'],
                balanced=True
            )

    return node_dict, storage_labels
