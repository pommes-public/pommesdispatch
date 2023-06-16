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


def load_input_data(filename=None, dm=None):
    r"""Load input data from csv files.

    Display some information on NaN values in time series data.

    Parameters
    ----------
    filename : :obj:`str`
        Name of .csv file containing data

    dm : :class:`DispatchModel`
        The dispatch model that is considered

    Returns
    -------
    df : :class:`pandas.DataFrame`
        DataFrame containing information about nodes or time series.
    """
    df = pd.read_csv(dm.path_folder_input + filename + ".csv", index_col=0)

    if "country" in df.columns and dm.countries is not None:
        df = df[df["country"].isin(dm.countries)]

    if df.isna().any().any() and "_ts" in filename:
        print(
            f"Attention! Time series input data file "
            f"{filename} contains NaNs."
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


def create_linking_transformers(input_data, dm, node_dict):
    r"""Create linking transformers and add them to the dict of nodes.

    Linking transformers serve for modeling interconnector capacities

    Parameters
    ----------
    input_data: :obj:`dict` of :class:`pd.DataFrame`
        The input data given as a dict of DataFrames
        with component names as keys

    dm : :class:`DispatchModel`
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
    for i, l in input_data["linking_transformers"].iterrows():
        try:
            if l["type"] == "DC":
                node_dict[i] = solph.components.Transformer(
                    label=i,
                    inputs={
                        node_dict[l["from"]]: solph.Flow(
                            nominal_value=l[dm.year]
                        )
                    },
                    outputs={node_dict[l["to"]]: solph.Flow()},
                    conversion_factors={
                        (node_dict[l["from"]], node_dict[l["to"]]): l[
                            "conversion_factor"
                        ]
                    },
                )

            if l["type"] == "AC":
                node_dict[i] = solph.components.Transformer(
                    label=i,
                    inputs={
                        node_dict[l["from"]]: solph.Flow(
                            nominal_value=l[dm.year],
                            max=input_data["linking_transformers_ts"]
                            .loc[
                                f"{dm.start_time}+00:00":f"{dm.end_time}"
                                f"+00:00",
                                i,
                            ]
                            .to_numpy(),
                        )
                    },
                    outputs={node_dict[l["to"]]: solph.Flow()},
                    conversion_factors={
                        (node_dict[l["from"]], node_dict[l["to"]]): l[
                            "conversion_factor"
                        ]
                    },
                )

        except KeyError:
            pass

    return node_dict


def create_commodity_sources(input_data, dm, node_dict):
    r"""Create commodity sources and add them to the dict of nodes.

    Parameters
    ----------
    input_data: :obj:`dict` of :class:`pd.DataFrame`
        The input data given as a dict of DataFrames
        with component names as keys

    dm : :class:`DispatchModel`
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
        node_dict[i] = solph.components.Source(
            label=i,
            outputs={
                node_dict[cs["to"]]: solph.Flow(
                    variable_costs=(
                        input_data["costs_fuel"].loc[i, dm.year]
                        + input_data["costs_emissions"].loc[i, dm.year]
                        * np.array(
                            input_data["costs_emissions_ts"]["price"][
                                dm.start_time : dm.end_time
                            ]
                        )
                        * cs["emission_factors"]
                    ),
                    emission_factor=cs["emission_factors"],
                )
            },
        )

    # Fluctuating renewables in Germany
    for i, cs in input_data["sources_renewables_fluc"].iterrows():
        node_dict[i] = solph.components.Source(
            label=i, outputs={node_dict[cs["to"]]: solph.Flow()}
        )

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
        node_dict[i] = solph.components.Source(
            label=i,
            outputs={
                node_dict[s["to"]]: solph.Flow(
                    variable_costs=s["shortage_costs"]
                )
            },
        )

    # Market-based shortage situations
    for i, s in input_data["sources_shortage_el_add"].iterrows():
        node_dict[i] = solph.components.Source(
            label=i,
            outputs={
                node_dict[s["to"]]: solph.Flow(
                    nominal_value=s["nominal_value"],
                    variable_costs=s["shortage_costs"],
                )
            },
        )

    return node_dict


def create_renewables(input_data, dm, node_dict):
    r"""Create renewable sources and add them to the dict of nodes.

    Parameters
    ----------
    input_data: :obj:`dict` of :class:`pd.DataFrame`
        The input data given as a dict of DataFrames
        with component names as keys

    dm : :class:`DispatchModel`
        The dispatch model that is considered

    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Dictionary containing all nodes of the EnergySystem

    Returns
    -------
    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Modified dictionary containing all nodes of the EnergySystem
        including the renewables source elements
    """
    for i, re in input_data["sources_renewables"].iterrows():
        try:
            node_dict[i] = solph.components.Source(
                label=i,
                outputs={
                    node_dict[re["to"]]: solph.Flow(
                        fix=np.array(
                            input_data["sources_renewables_ts"][i][
                                dm.start_time : dm.end_time
                            ]
                        ),
                        nominal_value=re["capacity"],
                    )
                },
            )
        except KeyError:
            print(re)

    return node_dict


def create_demand(input_data, dm, node_dict):
    r"""Create demand sinks and add them to the dict of nodes.

    Parameters
    ----------
    input_data: :obj:`dict` of :class:`pd.DataFrame`
        The input data given as a dict of DataFrames
        with component names as keys

    dm : :class:`DispatchModel`
        The dispatch model that is considered

    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Dictionary containing all nodes of the EnergySystem

    Returns
    -------
    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Modified dictionary containing all nodes of the EnergySystem
        including the demand sink elements
    """
    for i, d in input_data["sinks_demand_el"].iterrows():
        kwargs_dict = {
            "label": i,
            "inputs": {
                node_dict[d["from"]]: solph.Flow(
                    fix=np.array(
                        input_data["sinks_demand_el_ts"][i][
                            dm.start_time : dm.end_time
                        ]
                    ),
                    nominal_value=d["maximum"],
                )
            },
        }

        node_dict[i] = solph.components.Sink(**kwargs_dict)

    return node_dict


def create_demand_response_units(input_data, dm, node_dict):
    r"""Create demand response units and add them to the dict of nodes.

    The demand response modeling approach can be chosen from different
    approaches that have been implemented.

    Parameters
    ----------
    input_data: :obj:`dict` of :class:`pd.DataFrame`
        The input data given as a dict of DataFrames
        with component names as keys

    dm : :class:`DispatchModel`
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
    for dr_cluster, eligibility in input_data[
        "demand_response_clusters_eligibility"
    ].iterrows():
        # Introduce shortcut for demand response data set
        dr_cluster_potential_data = input_data[f"sinks_dr_el_{dr_cluster}"]
        dr_cluster_variable_costs_data = input_data[
            f"sinks_dr_el_{dr_cluster}_variable_costs"
        ]
        # Use 2020 as a year for simulating 2017 etc.
        simulation_year = max(2020, int(dm.start_time[:4]))

        # kwargs for all demand response modeling approaches
        kwargs_all = {
            "demand": np.array(
                input_data["sinks_dr_el_ts"][dr_cluster].loc[
                    dm.start_time : dm.end_time
                ]
            ),
            # max_capacity_up and max_capacity_down equal to potential
            # which assumed to be utilized
            "max_capacity_up": dr_cluster_potential_data.loc[
                simulation_year, "potential_neg_overall"
            ],
            "max_capacity_down": min(
                dr_cluster_potential_data.loc[
                    simulation_year, "potential_pos_overall"
                ],
                dr_cluster_potential_data.loc[simulation_year, "max_cap"],
            ),
            "capacity_up": np.array(
                input_data["sinks_dr_el_ava_neg_ts"][dr_cluster].loc[
                    dm.start_time : dm.end_time
                ]
            ),
            "capacity_down": np.array(
                input_data["sinks_dr_el_ava_pos_ts"][dr_cluster].loc[
                    dm.start_time : dm.end_time
                ]
            ),
            "max_demand": dr_cluster_potential_data.loc[
                simulation_year, "max_cap"
            ],
            "delay_time": math.ceil(
                dr_cluster_potential_data.at[2020, "shifting_duration"]
            ),
            "shed_time": math.ceil(
                dr_cluster_potential_data.at[
                    2020, "interference_duration_pos_shed"
                ]
            ),
            "recovery_time_shed": math.ceil(
                dr_cluster_potential_data.at[2020, "regeneration_duration"]
            ),
            "cost_dsm_up": dr_cluster_variable_costs_data.loc[
                f"{simulation_year}-01-01", "variable_costs"
            ]
            / 2,
            "cost_dsm_down_shift": dr_cluster_variable_costs_data.loc[
                f"{simulation_year}-01-01", "variable_costs"
            ]
            / 2,
            "cost_dsm_down_shed": dr_cluster_variable_costs_data.loc[
                f"{simulation_year}-01-01", "variable_costs_shed"
            ],
            "efficiency": 1,  # TODO: Replace hard-coded entries!
            "shed_eligibility": eligibility["shedding"],
            "shift_eligibility": eligibility["shifting"],
        }

        # kwargs dependent on demand response modeling approach chosen
        kwargs_dict = {
            "DIW": {
                "approach": "DIW",
                "recovery_time_shift": math.ceil(
                    dr_cluster_potential_data.at[2020, "regeneration_duration"]
                ),
            },
            "DLR": {
                "approach": "DLR",
                "shift_time": math.ceil(
                    dr_cluster_potential_data.at[2020, "shifting_duration"]
                ),
                "ActivateYearLimit": True,
                "ActivateDayLimit": False,
                "n_yearLimit_shift": np.max(
                    [
                        round(
                            dr_cluster_potential_data.at[
                                2020, "maximum_activations_year"
                            ]
                        ),
                        1,
                    ]
                ),
                "n_yearLimit_shed": np.max(
                    [
                        round(
                            dr_cluster_potential_data.at[
                                2020, "maximum_activations_year"
                            ]
                        ),
                        1,
                    ]
                ),
                "t_dayLimit": 24,
                "addition": True,
                "fixes": True,
            },
            "oemof": {"approach": "oemof", "shift_interval": 24},
        }

        node_dict[dr_cluster] = solph.components.experimental.SinkDSM(
            label=dr_cluster,
            inputs={
                node_dict[
                    dr_cluster_potential_data.at[2020, "from"]
                ]: solph.Flow(variable_costs=0)
            },
            **kwargs_all,
            **kwargs_dict[dm.demand_response_approach],
        )

    return node_dict


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
        node_dict[i] = solph.components.Sink(
            label=i,
            inputs={
                node_dict[e["from"]]: solph.Flow(
                    variable_costs=e["excess_costs"]
                )
            },
        )

    # The German sink is special due to a different input
    try:
        node_dict["DE_sink_el_excess"] = solph.components.Sink(
            label="DE_sink_el_excess",
            inputs={
                node_dict["DE_bus_windoffshore"]: solph.Flow(variable_costs=0),
                node_dict["DE_bus_windonshore"]: solph.Flow(variable_costs=0),
                node_dict["DE_bus_solarPV"]: solph.Flow(variable_costs=0),
            },
        )
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
    node_dict[i] = solph.components.Transformer(
        label=i,
        inputs={node_dict[t["from"]]: solph.Flow()},
        outputs={
            node_dict[t["to_el"]]: solph.Flow(**outflow_args_el),
            node_dict[t["to_th"]]: solph.Flow(**outflow_args_th),
        },
        conversion_factors={
            node_dict[t["to_el"]]: t["efficiency_el_CC"],
            node_dict[t["to_th"]]: t["efficiency_th_CC"],
        },
    )

    return node_dict[i]


def build_var_chp_units(i, t, node_dict, outflow_args_el, outflow_args_th):
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
    node_dict[i] = solph.components.ExtractionTurbineCHP(
        label=i,
        inputs={node_dict[t["from"]]: solph.Flow()},
        outputs={
            node_dict[t["to_el"]]: solph.Flow(**outflow_args_el),
            node_dict[t["to_th"]]: solph.Flow(**outflow_args_th),
        },
        conversion_factors={
            node_dict[t["to_el"]]: t["efficiency_el_CC"],
            node_dict[t["to_th"]]: t["efficiency_th_CC"],
        },
        conversion_factor_full_condensation={
            node_dict[t["to_el"]]: t["efficiency_el"]
        },
    )

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
    node_dict[i] = solph.components.Transformer(
        label=i,
        inputs={node_dict[t["from"]]: solph.Flow()},
        outputs={node_dict[t["to_el"]]: solph.Flow(**outflow_args_el)},
        conversion_factors={node_dict[t["to_el"]]: t["efficiency_el"]},
    )

    return node_dict[i]


def create_transformers_conventional(input_data, dm, node_dict):
    r"""Create transformers elements and add them to the dict of nodes

    Parameters
    ----------
    input_data: :obj:`dict` of :class:`pd.DataFrame`
        The input data given as a dict of DataFrames
        with component names as keys

    dm : :class:`DispatchModel`
        The dispatch model that is considered

    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Dictionary containing all nodes of the EnergySystem

    Returns
    -------
    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Modified dictionary containing all nodes of the EnergySystem
        including the demand sink elements
    """
    for i, t in input_data["transformers"].iterrows():
        outflow_args_el = {
            "nominal_value": t["capacity"],
            "variable_costs": (
                input_data["costs_operation"].loc[t["from"], dm.year]
            ),
            "min": t["min_load_factor"],
            "max": (t["max_load_factor"]),
            "positive_gradient": {"ub": t["grad_pos"]},
            "negative_gradient": {"ub": t["grad_neg"]},
        }

        # Assign minimum loads and gradients for German CHP and IPP plants
        if t["country"] == "DE":
            if t["type"] == "chp":
                if t["identifier"] in input_data["min_loads_dh"].columns:
                    set_min_load_and_gradient_profile(
                        t,
                        outflow_args_el,
                        input_data,
                        dm,
                        min_load_ts="min_loads_dh",
                        min_load_column=t["identifier"],
                        gradient_ts="dh_gradients_ts",
                        gradient_column=t["identifier"],
                    )
                elif t["fuel"] in ["natgas", "hardcoal", "lignite"]:
                    set_min_load_and_gradient_profile(
                        t,
                        outflow_args_el,
                        input_data,
                        dm,
                        min_load_ts="transformers_minload_ts",
                        min_load_column="chp_" + t["fuel"],
                        gradient_ts="remaining_gradients_ts",
                        gradient_column="chp_" + t["fuel"],
                    )
                else:
                    set_min_load_and_gradient_profile(
                        t,
                        outflow_args_el,
                        input_data,
                        dm,
                        min_load_ts="transformers_minload_ts",
                        min_load_column="chp",
                        gradient_ts="remaining_gradients_ts",
                        gradient_column="chp_" + t["fuel"],
                    )

            if t["type"] == "ipp":
                if t["identifier"] in input_data["min_loads_ipp"].columns:
                    set_min_load_and_gradient_profile(
                        t,
                        outflow_args_el,
                        input_data,
                        dm,
                        min_load_ts="min_loads_ipp",
                        min_load_column=t["identifier"],
                        gradient_ts="ipp_gradients_ts",
                        gradient_column=t["identifier"],
                    )
                else:
                    set_min_load_and_gradient_profile(
                        t,
                        outflow_args_el,
                        input_data,
                        dm,
                        min_load_ts="transformers_minload_ts",
                        min_load_column="ipp",
                        gradient_ts="remaining_gradients_ts",
                        gradient_column="ipp_" + t["fuel"],
                    )

        # Limit flexibility for Austrian and French natgas plants
        if t["country"] in ["AT", "FR"] and t["fuel"] == "natgas":
            set_min_load_and_gradient_profile(
                t,
                outflow_args_el,
                input_data,
                dm,
                min_load_ts="transformers_minload_ts",
                min_load_column=t["country"] + "_natgas",
                gradient_ts="remaining_gradients_ts",
                gradient_column=t["country"] + "_natgas",
            )
            outflow_args_el["max"] = np.minimum(
                [1]
                * len(
                    input_data["transformers_minload_ts"].loc[
                        dm.start_time : dm.end_time
                    ]
                ),
                input_data["transformers_minload_ts"]
                .loc[
                    dm.start_time : dm.end_time,
                    t["country"] + "_natgas",
                ]
                .to_numpy()
                + 0.01,
            )

        # Introduce availability and handle minimum loads
        else:
            outflow_args_el["max"] = np.minimum(
                [1]
                * len(
                    input_data["transformers_availability_ts"].loc[
                        dm.start_time : dm.end_time
                    ]
                ),
                np.maximum(
                    outflow_args_el["min"] + 0.01,
                    outflow_args_el["max"]
                    * np.array(
                        input_data["transformers_availability_ts"][
                            "values"
                        ].loc[dm.start_time : dm.end_time]
                    ),
                ),
            )

        outflow_args_el["negative_gradient"] = outflow_args_el[
            "positive_gradient"
        ]

        node_dict[i] = build_condensing_transformer(
            i, t, node_dict, outflow_args_el
        )

    return node_dict


def set_min_load_and_gradient_profile(
    t,
    outflow_args_el,
    input_data,
    dm,
    min_load_ts,
    min_load_column,
    gradient_ts,
    gradient_column,
    availability_ts="transformers_availability_ts",
):
    """Set the min load and gradient profile of a transformer

    Parameters
    ----------
    t : pd.Series
        parameter data for the transformer to create

    outflow_args_el : dict
        dictionary of transformer outflow arguments

    input_data: :obj:`dict` of :class:`pd.DataFrame`
        The input data given as a dict of DataFrames
        with component names as keys

    dm : :class:`DispatchModel`
        The dispatch model that is considered

    min_load_ts : str
        Dictionary key for the minimum load time series DataFrame

    min_load_column : str
        Name of the column to use for assigning the minimum load profile

    gradient_ts : str
        Dictionary key for the gradients time series DataFrame

    gradient_column : str
        Name of the column to use for assigning the gradient profile

    availability_ts : str
        Name of the column to use for limiting minimum output with current
        availability
    """
    outflow_args_el["min"] = np.minimum(
        input_data[min_load_ts]
        .loc[
            dm.start_time : dm.end_time,
            min_load_column,
        ]
        .to_numpy(),
        input_data[availability_ts]
        .loc[dm.start_time : dm.end_time, "values"]
        .to_numpy()
        - 0.01,
    )
    outflow_args_el["positive_gradient"]["ub"] = (
        input_data[gradient_ts]
        .loc[
            dm.start_time : dm.end_time,
            gradient_column,
        ]
        .to_numpy()
    )


def create_transformers_res(input_data, dm, node_dict):
    r"""Create renewable energy transformers and add them to the dict of nodes.

    Parameters
    ----------
    input_data: :obj:`dict` of :class:`pd.DataFrame`
        The input data given as a dict of DataFrames
        with component names as keys

    dm : :class:`DispatchModel`
        The dispatch model that is considered

    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Dictionary containing all nodes of the EnergySystem

    Returns
    -------
    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Modified dictionary containing all nodes of the EnergySystem
        including the renewable transformer elements
    """
    for i, t in input_data["transformers_renewables"].iterrows():
        outflow_args_el = {
            "nominal_value": t["capacity"],
            "variable_costs": (
                input_data["costs_operation_renewables"].at[i, "costs"]
                + np.array(
                    input_data["costs_market_values"][t["from"]][
                        dm.start_time : dm.end_time
                    ]
                )
            ),
            "min": t["min_load_factor"],
            "max": np.array(
                input_data["sources_renewables_ts"][t["from"]][
                    dm.start_time : dm.end_time
                ]
            ),
            "positive_gradient": {"ub": t["grad_pos"]},
            "negative_gradient": {"ub": t["grad_neg"]},
        }

        node_dict[i] = solph.components.Transformer(
            label=i,
            inputs={node_dict[t["from"]]: solph.Flow()},
            outputs={node_dict[t["to_el"]]: solph.Flow(**outflow_args_el)},
            conversion_factors={node_dict[t["to_el"]]: t["efficiency_el"]},
        )

    return node_dict


def create_storages(input_data, dm, node_dict):
    r"""Create storages and add them to the dict of nodes.

    Parameters
    ----------
    input_data: :obj:`dict` of :class:`pd.DataFrame`
        The input data given as a dict of DataFrames
        with component names as keys

    dm : :class:`DispatchModel`
        The dispatch model that is considered

    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Dictionary containing all nodes of the EnergySystem

    Returns
    -------
    node_dict : :obj:`dict` of :class:`nodes <oemof.network.Node>`
        Modified dictionary containing all nodes of the EnergySystem
        including the storage elements
    """
    for i, s in input_data["storages_el"].iterrows():
        if s["type"] == "phes":
            node_dict[i] = solph.components.GenericStorage(
                label=i,
                inputs={
                    node_dict[s["bus_inflow"]]: solph.Flow(
                        nominal_value=s["capacity_pump"],
                        variable_costs=(
                            input_data["costs_operation_storages"].loc[
                                i, dm.year
                            ]
                        ),
                    )
                },
                outputs={
                    node_dict[s["bus_outflow"]]: solph.Flow(
                        nominal_value=s["capacity_turbine"],
                        variable_costs=(
                            input_data["costs_operation_storages"].loc[
                                i, dm.year
                            ]
                        ),
                    )
                },
                nominal_storage_capacity=s["nominal_storable_energy"],
                loss_rate=s["loss_rate"],
                initial_storage_level=s["initial_storage_level"],
                max_storage_level=s["max_storage_level"],
                min_storage_level=s["min_storage_level"],
                inflow_conversion_factor=s["efficiency_pump"],
                outflow_conversion_factor=s["efficiency_turbine"],
                balanced=True,
            )

        if s["type"] == "reservoir":
            node_dict[i] = solph.components.GenericStorage(
                label=i,
                inputs={node_dict[s["bus_inflow"]]: solph.Flow()},
                outputs={
                    node_dict[s["bus_outflow"]]: solph.Flow(
                        nominal_value=s["capacity_turbine"],
                        variable_costs=(
                            input_data["costs_operation_storages"].loc[
                                i, dm.year
                            ]
                        ),
                        min=s["min_load_factor"],
                        max=s["max_load_factor"],
                    )
                },
                nominal_storage_capacity=s["nominal_storable_energy"],
                loss_rate=s["loss_rate"],
                initial_storage_level=s["initial_storage_level"],
                max_storage_level=s["max_storage_level"],
                min_storage_level=s["min_storage_level"],
                inflow_conversion_factor=s["efficiency_pump"],
                outflow_conversion_factor=s["efficiency_turbine"],
                balanced=True,
            )

    return node_dict


def create_storages_rolling_horizon(
    input_data, dm, node_dict, iteration_results
):
    r"""Create storages, add them to the dict of nodes, return storage labels.

    Parameters
    ----------
    input_data: :obj:`dict` of :class:`pd.DataFrame`
        The input data given as a dict of DataFrames
        with component names as keys

    dm : :class:`DispatchModel`
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

    for i, s in input_data["storages_el"].iterrows():
        storage_labels.append(i)
        if not iteration_results["storages_initial"].empty:
            initial_storage_level_last_iteration = (
                iteration_results["storages_initial"].loc[
                    i, "initial_storage_level_last_iteration"
                ]
                / s["nominal_storable_energy"]
            )
        else:
            initial_storage_level_last_iteration = s["initial_storage_level"]

        if s["type"] == "phes":
            node_dict[i] = solph.components.GenericStorage(
                label=i,
                inputs={
                    node_dict[s["bus_inflow"]]: solph.Flow(
                        nominal_value=s["capacity_pump"],
                        variable_costs=(
                            input_data["costs_operation_storages"].loc[
                                i, dm.year
                            ]
                        ),
                    )
                },
                outputs={
                    node_dict[s["bus_outflow"]]: solph.Flow(
                        nominal_value=s["capacity_turbine"],
                        variable_costs=(
                            input_data["costs_operation_storages"].loc[
                                i, dm.year
                            ]
                        ),
                    )
                },
                nominal_storage_capacity=s["nominal_storable_energy"],
                loss_rate=s["loss_rate"],
                initial_storage_level=initial_storage_level_last_iteration,
                max_storage_level=s["max_storage_level"],
                min_storage_level=s["min_storage_level"],
                inflow_conversion_factor=s["efficiency_pump"],
                outflow_conversion_factor=s["efficiency_turbine"],
                balanced=True,
            )

        if s["type"] == "reservoir":
            node_dict[i] = solph.components.GenericStorage(
                label=i,
                inputs={node_dict[s["bus_inflow"]]: solph.Flow()},
                outputs={
                    node_dict[s["bus_outflow"]]: solph.Flow(
                        nominal_value=s["capacity_turbine"],
                        variable_costs=(
                            input_data["costs_operation_storages"].loc[
                                i, dm.year
                            ]
                        ),
                        min=s["min_load_factor"],
                        max=s["max_load_factor"],
                    )
                },
                nominal_storage_capacity=s["nominal_storable_energy"],
                loss_rate=s["loss_rate"],
                initial_storage_level=initial_storage_level_last_iteration,
                max_storage_level=s["max_storage_level"],
                min_storage_level=s["min_storage_level"],
                inflow_conversion_factor=s["efficiency_pump"],
                outflow_conversion_factor=s["efficiency_turbine"],
                balanced=True,
            )

    return node_dict, storage_labels
