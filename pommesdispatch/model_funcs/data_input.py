# -*- coding: utf-8 -*-
"""
General description
-------------------
This file contains all function definitions for reading in input data
used for the dispatch variant of POMMES.

@author: Johannes Kochems (*), Yannick Werner (*), Johannes Giehl,
Benjamin Grosse

Contributors:
Sophie Westphal, Flora von Mikulicz-Radecki, Carla Spiller, Fabian Büllesbach,
Timona Ghosh, Paul Verwiebe, Leticia Encinas Rosa, Joachim Müller-Kirchenbauer

(*) Corresponding authors
"""
import pandas as pd

from pommesdispatch.model_funcs import helpers
from pommesdispatch.model_funcs.subroutines import (
    load_input_data,
    create_buses,
    create_demand,
    create_storages,
    create_linking_transformers,
    create_transformers_conventional,
    create_renewables,
    create_commodity_sources,
    create_shortage_sources,
    create_excess_sinks,
    create_storages_rolling_horizon,
    create_transformers_res,
    create_demand_response_units,
)


def parse_input_data(dm):
    r"""Read in csv files as DataFrames and store them in a dict

    Parameters
    ----------
    dm : :class:`DispatchModel`
        The dispatch model that is considered

    Returns
    -------
    input_data: :obj:`dict` of :class:`pd.DataFrame`
        The input data given as a dict of DataFrames
        with component names as keys
    """
    buses = {
        "buses": "buses",
    }

    components = {
        "linking_transformers": "linking_transformers",
        "sinks_excess": "sinks_excess",
        "sinks_demand_el": "sinks_demand_el",
        "sources_shortage": "sources_shortage",
        "sources_shortage_el_add": "sources_shortage_el_add",
        "sources_renewables_fluc": "sources_fluc_res",
        "sources_commodity": "sources_commodity",
        "sources_renewables": "sources_renewables",
        "storages_el": "storages_el",
        "transformers": "transformers",
        "transformers_renewables": (
            f"transformers_renewables_"
            f"{dm.eeg_clusters_per_technology}_clusters"
        ),
    }

    time_series = {
        "linking_transformers_ts": "linking_transformers_ts",
        "sinks_demand_el_ts": "sinks_demand_el_ts_hourly",
        "costs_market_values": (
            f"costs_market_values_{dm.eeg_clusters_per_technology}_clusters"
        ),
        "sources_renewables_ts": "sources_renewables_ts",
        "transformers_minload_ts": "transformers_minload_ts",
        "transformers_availability_ts": "transformers_availability_ts",
        "costs_fuel": f"costs_fuel_{dm.fuel_cost_pathway}_nominal",
        "costs_fuel_ts": "costs_fuel_ts",
        "costs_emissions": (
            f"costs_emissions_{dm.emissions_cost_pathway}_nominal"
        ),
        "costs_emissions_ts": "costs_emissions_ts",
        "costs_operation": "costs_operation_nominal",
        "costs_operation_renewables": (
            f"costs_operation_renewables_"
            f"{dm.eeg_clusters_per_technology}_clusters"
        ),
        "costs_operation_storages": "costs_operation_storages_nominal",
        "min_loads_dh": "min_loads_dh",
        "min_loads_ipp": "min_loads_ipp",
        "dh_gradients_ts": "dh_gradients_ts",
        "ipp_gradients_ts": "ipp_gradients_ts",
        "remaining_gradients_ts": "remaining_gradients_ts",
    }

    other_files = {"emission_limits": "emission_limits"}

    # Optionally use aggregated transformer data instead
    if dm.aggregate_input:
        components["transformers"] = "transformers_clustered"

    # Add demand response units
    if dm.activate_demand_response:
        # Overall demand = overall demand excluding demand response baseline
        time_series["sinks_demand_el_ts"] = (
            f"sinks_demand_el_excl_demand_response_ts_"
            f"{dm.demand_response_scenario}_hourly"
        )
        other_files["sinks_demand_el"] = (
            f"sinks_demand_el_excl_demand_response_"
            f"{dm.demand_response_scenario}"
        )

        # Obtain demand response clusters from file to avoid hard-coding
        other_files[
            "demand_response_clusters_eligibility"
        ] = "demand_response_clusters_eligibility"
        dr_clusters = load_input_data(
            filename="demand_response_clusters_eligibility", dm=dm
        )
        # Add demand response clusters information to the model itself
        dm.add_demand_response_clusters(list(dr_clusters.index))
        for dr_cluster in dr_clusters.index:
            other_files[f"sinks_dr_el_{dr_cluster}"] = (
                f"{dr_cluster}_potential_parameters_"
                f"{dm.demand_response_scenario}%"
            )
            other_files[f"sinks_dr_el_{dr_cluster}_variable_costs"] = (
                f"{dr_cluster}_variable_costs_parameters_"
                f"{dm.demand_response_scenario}%"
            )

        time_series[
            "sinks_dr_el_ts"
        ] = f"sinks_demand_response_el_ts_{dm.demand_response_scenario}"

        time_series["sinks_dr_el_ava_pos_ts"] = (
            f"sinks_demand_response_el_ava_pos_ts_"
            f"{dm.demand_response_scenario}"
        )
        time_series["sinks_dr_el_ava_neg_ts"] = (
            f"sinks_demand_response_el_ava_neg_ts_"
            f"{dm.demand_response_scenario}"
        )

    # Combine all files
    input_files = {**buses, **components, **time_series}

    # Use data for the respective simulation year
    input_files = {k: v + "_" + dm.year for k, v in input_files.items()}
    input_files = {**input_files, **other_files}

    input_data = {
        key: load_input_data(
            filename=name,
            dm=dm,
        )
        for key, name in input_files.items()
    }

    return input_data


def add_components(input_data, dispatch_model):
    r"""Add the oemof components to a dictionary of nodes

    Note: Storages are not included here. They have to be defined
    separately since the approaches differ between rolling horizon
    and simple model.

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

    node_dict = create_linking_transformers(
        input_data, dispatch_model, node_dict
    )

    # Also creates fluctuating RES sources for Germany
    node_dict = create_commodity_sources(input_data, dispatch_model, node_dict)

    node_dict = create_shortage_sources(input_data, node_dict)

    node_dict = create_renewables(input_data, dispatch_model, node_dict)

    # create sinks
    if dispatch_model.activate_demand_response:
        node_dict = create_demand_response_units(
            input_data, dispatch_model, node_dict
        )

        node_dict = create_demand(input_data, dispatch_model, node_dict)
    else:
        node_dict = create_demand(input_data, dispatch_model, node_dict)

    node_dict = create_excess_sinks(input_data, node_dict)

    # create conventional transformers
    node_dict = create_transformers_conventional(
        input_data, dispatch_model, node_dict
    )

    # create renewable transformers
    node_dict = create_transformers_res(input_data, dispatch_model, node_dict)

    return node_dict


def add_limits(
    input_data,
    emissions_pathway,
    start_time="2017-01-01 00:00:00",
    end_time="2017-01-01 23:00:00",
):
    r"""Add further limits to the optimization model (emissions limit for now)

    Parameters
    ----------
    input_data: :obj:`dict` of :class:`pd.DataFrame`
        The input data given as a dict of DataFrames
        with component names as keys

    emissions_pathway : str
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
        input_data["emission_limits"][emissions_pathway], start_time, end_time
    )

    return emissions_limit


def nodes_from_csv(dispatch_model):
    r"""Build oemof.solph components from input data

    Parameters
    ----------
    dispatch_model : :class:`DispatchModel`
        The dispatch model that is considered

    Returns
    -------
    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Dictionary containing all nodes of the EnergySystem

    emissions_limit : int or None
        The overall emissions limit
    """
    input_data = parse_input_data(dispatch_model)

    node_dict = add_components(input_data, dispatch_model)

    node_dict = create_storages(input_data, dispatch_model, node_dict)

    emissions_limit = None
    if dispatch_model.activate_emissions_limit:
        emissions_limit = add_limits(
            input_data,
            dispatch_model.emissions_pathway,
            dispatch_model.start_time,
            dispatch_model.end_time,
        )

    return node_dict, emissions_limit


def nodes_from_csv_rh(dispatch_model, iteration_results):
    r"""Read in csv files and build components for a rolling horizon run

    Parameters
    ----------
    dispatch_model : :class:`DispatchModel`
        The dispatch model that is considered

    iteration_results : dict
        A dictionary holding the results of the previous rolling horizon
        iteration

    Returns
    -------
    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Dictionary containing all nodes of the EnergySystem

    emissions_limit : int or None
        The overall emissions limit

    storage_labels : :obj:`list` of :class:`str`
        A list of the labels of all storage elements included in the model
        used for assessing these and assigning initial states
    """
    frequency_used = {
        "60min": (
            getattr(dispatch_model, "time_slice_length_with_overlap"),
            "h",
        ),
        "15min": (
            getattr(dispatch_model, "time_slice_length_with_overlap") * 15,
            "min",
        ),
    }[dispatch_model.freq]

    # Update start time and end time of the model for retrieving the right data
    dispatch_model.start_time = getattr(
        dispatch_model, "time_series_start"
    ).strftime("%Y-%m-%d %H:%M:%S")
    dispatch_model.end_time = (
        getattr(dispatch_model, "time_series_start")
        + pd.to_timedelta(frequency_used[0], frequency_used[1])
    ).strftime("%Y-%m-%d %H:%M:%S")

    input_data = parse_input_data(dispatch_model)

    node_dict = add_components(input_data, dispatch_model)

    # create storages (Rolling horizon)
    node_dict, storage_labels = create_storages_rolling_horizon(
        input_data, dispatch_model, node_dict, iteration_results
    )

    emissions_limit = None
    if dispatch_model.activate_emissions_limit:
        emissions_limit = add_limits(
            input_data,
            dispatch_model.emissions_pathway,
            dispatch_model.start_time,
            dispatch_model.end_time,
        )

    return node_dict, emissions_limit, storage_labels
