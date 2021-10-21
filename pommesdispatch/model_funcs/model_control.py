# -*- coding: utf-8 -*-
"""
General description
-------------------
This file contains all class and function definitions for controlling the model
workflow of the dispatch variant of POMMES.

@author: Johannes Kochems (*), Yannick Werner (*), Johannes Giehl,
Benjamin Grosse

Contributors:
Sophie Westphal, Flora von Mikulicz-Radecki, Carla Spiller, Fabian Büllesbach,
Timona Ghosh, Paul Verwiebe, Leticia Encinas Rosa, Joachim Müller-Kirchenbauer

(*) Corresponding authors
"""

import logging
import math

import pandas as pd
from oemof.solph import (constraints, views,
                         models, network, processing)
from oemof.tools import logger

from pommesdispatch.model_funcs import helpers
from pommesdispatch.model_funcs.data_input import (nodes_from_csv,
                                                   nodes_from_csv_rh)


def show_meta_logging_info(model_meta):
    """Show some logging information on model meta data"""
    logging.info(f"***** MODEL RUN TERMINATED SUCCESSFULLY :-) *****")
    logging.info(f"Overall objective value: "
                 + f"{model_meta['overall_objective']:,.0f}")
    logging.info(f"Overall solution time: "
                 + f"{model_meta['overall_solution_time']:.2f}")
    logging.info(f"Overall time: "
                 + f"{model_meta['overall_time']:.2f}")


class DispatchModel(object):
    """A class that holds a dispatch model.

    A dispatch model is a container for all the model parameters as well
    as for methods for controlling the model workflow.

    Attributes
    ----------
    rolling_horizon : boolean
        boolean control variable indicating whether to run a rolling horizon
        optimization or an integral optimization run (a simple model).
        Note: For the rolling_horizon optimization run, additionally the
        parameters `time_slice_length_wo_overlap_in_hours` and
        `overlap_in_hours` (both of type int) have to be defined.

    aggregate_input : boolean
        boolean control variable indicating whether to use complete
        or aggregated transformer input data set

    countries : list of str
        List of countries to be simulated

    solver : str
        The solver to be used for solving the mathematical optimization model.
        Must be one of the solvers oemof.solph resp. pyomo support, e.g.
        'cbc', 'gplk', 'gurobi', 'cplex'.

    fuel_cost_pathway :  str
       A predefined pathway for commodity cost develoment until 2050
        Options: 'lower', 'middle', 'upper'

    activate_emissions_limit : boolean
        boolean control variable indicating whether to introduce an overall
        emissions limit
        Note: Combining an emissions limit with comparatively high minimum
        loads of conventionals may lead to an infeasible model configuration
        since either one of the restrictions may not be reached.

    emissions_pathway : str
        A predefined pathway for emissions reduction until 2050
        Options: '100_percent_linear', '95_percent_linear', '80_percent_linear'
        or 'BAU'

    activate_demand_response : boolean
        boolean control variable indicating whether to introduce
        demand response to the model

    demand_response_approach : str
        The approach used for demand response modeling
        Options: 'DLR', 'DIW', 'oemof'
        See the documentation of the custom SinkDSM in oemof.solph as well
        as the presentation by Johannes Kochems from the INREC 2020
        for further information

    demand_response_scenario : str
        A predefined demand response scenario to be modeled
        Options: '25', '50', '75', whereby '25' is the lower,
        i.e. rather pessimistic estimate

    save_production_results : boolean
        boolean control variable indicating whether to save the dispatch
        results of the model run to a .csv file

    save_price_results : boolean
        boolean control variable indicating whether to save the power price
        results of the model run to a .csv file

    write_lp_file : boolean
        boolean control variable indicating whether to save an lp file
        *CAUTION*: Only use for debugging when simulating small time frames

    start_time : str
        A date string of format "YYYY-MM-DD hh:mm:ss" defining the start time
        of the simulation

    end_time : str
        A date string of format "YYYY-MM-DD hh:mm:ss" defining the end time
        of the simulation

    path_folder_input : str
        The path to the folder where the input data is stored

    path_folder_output : str
        The path to the folder where the output data is to be stored

    om : :class:`oemof.solph.models.Model`
        The mathematical optimization model itself

    time_slice_length_wo_overlap_in_hours : int (optional, for rolling horizon)
        The length of a time slice for a rolling horizon model run in hours,
        not including an overlap

    overlap_in_hours : int (optional, for rolling horizon)
        The length of the overlap for a rolling horizon model run in hours
    """

    def __init__(self):
        """Initialize an empty DispatchModel object"""
        self.rolling_horizon = None
        self.aggregate_input = None
        self.countries = None
        self.solver = None
        self.fuel_cost_pathway = None
        self.activate_emissions_limit = None
        self.emissions_pathway = None
        self.activate_demand_response = None
        self.demand_response_approach = None
        self.demand_response_scenario = None
        self.save_production_results = None
        self.save_price_results = None
        self.write_lp_file = None
        self.start_time = None
        self.end_time = None
        self.freq = None
        self.path_folder_input = None
        self.path_folder_output = None
        self.om = None

    def update_model_configuration(self, *model_parameters, nolog=False):
        """Set the main model parameters by extracting them from dicts

        Parameters
        ----------
        *model_parameters : dict
            An arbitrary amount of dicts holding the model parameterization
            information

        nolog : boolean
            Show no logging ingo if True; else show logs for updating resp.
            adding attributes to the dispatch model
        """
        for param_dict in model_parameters:
            for k, v in param_dict.items():
                if not nolog:
                    if hasattr(self, k):
                        print(
                            f"Updating attribute `{k}` with value '{v}'.")
                    else:
                        print(
                            f"Adding attribute `{k}` with value '{v}' "
                            + "to the model.")
                setattr(self, k, v)

        if hasattr(self, "start_time"):
            setattr(self, "year", str(pd.to_datetime(self.start_time).year))

    def check_model_configuration(self):
        """Checks if any necessary model parameter hasn't been set yet"""
        missing_parameters = []

        for entry in dir(self):
            if not entry.startswith("_"):
                if entry != "om" and getattr(self, entry) is None:
                    missing_parameters.append(entry)
                    logging.warning(
                        f"Necessary model parameter `{entry}` "
                        + "has not yet been specified!")

        return missing_parameters

    def add_rolling_horizon_configuration(self, rolling_horizon_parameters,
                                          nolog=False):
        """Add a rolling horizon configuration to the dispatch model"""
        self.update_model_configuration(rolling_horizon_parameters,
                                        nolog=nolog)

        setattr(self, "time_series_start",
                pd.Timestamp(self.start_time, self.freq))
        setattr(self, "time_series_end",
                pd.Timestamp(self.end_time, self.freq))
        setattr(self, "time_slice_length_wo_overlap_in_time_steps",
                ({'60min': 1, '15min': 4}[self.freq]
                 * getattr(self, "time_slice_length_wo_overlap_in_hours")))
        setattr(self, "overlap_in_time_steps",
                ({'60min': 1, '15min': 4}[self.freq]
                 * getattr(self, "overlap_in_hours")))
        setattr(self, "time_slice_length_with_overlap",
                (getattr(self, "time_slice_length_wo_overlap_in_time_steps")
                 + getattr(self, "overlap_in_time_steps")))
        setattr(self, "overall_time_steps",
                helpers.time_steps_between_timestamps(
                    getattr(self, "time_series_start"),
                    getattr(self, "time_series_end"),
                    self.freq))
        setattr(self, "amount_of_time_slices",
                math.ceil(
                    getattr(self, "overall_time_steps")
                    / getattr(self,
                              "time_slice_length_wo_overlap_in_time_steps")))

    def initialize_logging(self):
        """Initialize logging by deriving a filename from the configuration"""
        optimization_timeframe = helpers.days_between(self.start_time,
                                                      self.end_time)

        if not self.rolling_horizon:
            rh = 'simple_'
        else:
            rh = 'RH_'
        if self.aggregate_input:
            agg = 'clustered'
        else:
            agg = 'complete'

        filename = ("dispatch_LP_start-" + self.start_time[:10] + "_"
                    + str(optimization_timeframe) + "-days_" + rh + agg)

        setattr(self, "filename", filename)
        logger.define_logging(logfile=filename + ".log")

        return filename

    def show_configuration_log(self):
        """Show some logging info dependent on model configuration"""
        if self.aggregate_input:
            agg_string = "Using the AGGREGATED POWER PLANT DATA SET"
        else:
            agg_string = ("Using the COMPLETE POWER PLANT DATA SET.\n"
                          "Minimum power output constraint of (individual)\n"
                          "transformers will be neglected.")

        if self.activate_demand_response:
            dr_string = (
                f"Using approach '{self.demand_response_approach}' "
                f"for DEMAND RESPONSE modeling\n"
                f"Considering a {self.demand_response_scenario}% scenario")

        else:
            dr_string = "Running a model WITHOUT DEMAND RESPONSE"

        logging.info(agg_string)
        logging.info(dr_string)

        return agg_string, dr_string

    def build_simple_model(self):
        r"""Set up and return a simple model

        Construct a model for an overall optimization run
        not including any measures for complexity reduction.
        """
        logging.info('Starting optimization')
        logging.info('Running a DISPATCH OPTIMIZATION')

        datetime_index = pd.date_range(
            self.start_time, self.end_time, freq=self.freq)
        es = network.EnergySystem(timeindex=datetime_index)

        nodes_dict, emissions_limit = nodes_from_csv(self)

        logging.info('Creating a LP model for DISPATCH OPTIMIZATION.')

        es.add(*nodes_dict.values())
        setattr(self, "om", models.Model(es))

        self.add_further_constrs(
            emissions_limit)

    def add_further_constrs(
            self,
            emissions_limit,
            countries=None,
            fuels=None):
        r"""Integrate further constraints into the optimization model

        For now, an additional overall emissions limit can be imposed.

        Note that setting an emissions limit may conflict with high minimum
        loads from conventional transformers.
        Be aware that this may lead to model infeasibility
        if commodity bus balances cannot be met.

        Parameters
        ----------
        emissions_limit : float
            The actual emissions limit to be used

        countries : :obj:`list` of `str`
            The countries for which an emissions limit shall be imposed
            (Usually only Germany, so ["DE"])

        fuels : :obj:`list` of `str`
            The fuels for which an emissions limit shall be imposed
        """
        if countries is None:
            countries = ["DE"]

        if fuels is None:
            fuels = ["biomass", "hardcoal", "lignite",
                     "natgas", "uranium", "oil",
                     "otherfossil", "waste", "mixedfuels"]

        # Emissions limit is imposed for flows from commodity source to bus
        emission_flow_labels = [country + '_bus_' + fuel
                                for country in countries
                                for fuel in fuels]

        emission_flows = {}

        for (i, o) in self.om.flows:
            if any(x in o.label for x in emission_flow_labels):
                emission_flows[(i, o)] = self.om.flows[(i, o)]

        if self.activate_emissions_limit:
            constraints.emission_limit(self.om, flows=emission_flows,
                                       limit=emissions_limit)
            logging.info(
                f"Adding an EMISSIONS LIMIT of {emissions_limit} t CO2")

    def get_power_prices_from_duals(self):
        r"""Obtain the power price results for the dispatch model

        The power prices are obtained from the dual value of the
        Bus.balance constraint of the German electricity bus.

        Returns
        -------
        power_prices: :obj:`pd.DataFrame`
        """
        constr = self.om.Bus.balance

        power_prices_list = [self.om.dual[constr[index]]
                             for index in constr if
                             index[0].label == "DE_bus_el"]
        power_prices = pd.DataFrame(data=power_prices_list,
                                    index=self.om.es.timeindex,
                                    columns=["Power price"])

        return power_prices

    def build_rolling_horizon_model(self, counter, iteration_results):
        r"""Set up and return a rolling horizon LP dispatch model

        Track the storage labels in order to obtain and pass initial
        storage levels for each iteration. Set the end time of an iteration
        excluding the overlap to the start of the next iteration.

        Parameters
        ----------
        counter : int
            A counter for the rolling horizon optimization iterations

        iteration_results : dict
            A dictionary holding the results of the previous rolling horizon
            iteration
        """
        setattr(self, "time_series_end",
                (getattr(self, "time_series_start")
                 + pd.to_timedelta(
                            getattr(
                                self,
                                "time_slice_length_wo_overlap_in_hours"),
                            "h")))

        logging.info(f"Starting optimization for optimization run {counter}")
        logging.info(f"Start of iteration {counter}: "
                     + f"{getattr(self, 'time_series_start')}")
        logging.info(f"End of iteration {counter}: "
                     + f"{getattr(self, 'time_series_end')}")

        datetime_index = pd.date_range(
            start=getattr(self, "time_series_start"),
            periods=getattr(self, "time_slice_length_with_overlap"),
            freq=self.freq)
        es = network.EnergySystem(timeindex=datetime_index)

        node_dict, emissions_limit, storage_labels = nodes_from_csv_rh(
            self, iteration_results)
        # Only set storage labels attribute for the 0th iteration
        if not hasattr(self, "storage_labels"):
            setattr(self, "storage_labels", storage_labels)

        # Update model start time for the next iteration
        setattr(self, "time_series_start", getattr(self, "time_series_end"))

        es.add(*node_dict.values())
        logging.info(
            f"Successfully set up energy system for iteration {counter}")

        self.om = models.Model(es)

        self.add_further_constrs(emissions_limit)

    def solve_rolling_horizon_model(self, counter, iteration_results,
                                    model_meta, no_solver_log=False):
        """Solve a rolling horizon optimization model

        Parameters
        ----------
        counter : int
            A counter for the rolling horizon optimization iterations

        iteration_results : dict
            A dictionary holding the results of the previous rolling horizon
            iteration

        model_meta : dict
            A dictionary holding meta information on the model, such as
             solution times and objective value
        """
        self.om.receive_duals()
        logging.info(
            "Obtaining dual values and reduced costs from the model \n"
            "in order to calculate power prices.")

        if self.write_lp_file:
            self.om.write((self.path_folder_output
                           + "pommesdispatch_model_iteration_" + str(counter)
                           + ".lp"),
                          io_options={"symbolic_solver_labels": True})

        if no_solver_log:
            solve_kwargs = {'tee': False}
        else:
            solve_kwargs = {'tee': True}

        self.om.solve(solver=self.solver, solve_kwargs=solve_kwargs)
        print("********************************************************")
        logging.info(f"Model run {counter} done!")

        iteration_results["model_results"] = processing.results(self.om)
        electricity_bus = views.node(iteration_results["model_results"],
                                     "DE_bus_el")
        sliced_dispatch_results = pd.DataFrame(
            data=electricity_bus["sequences"].iloc[
                 0:getattr(self,
                           "time_slice_length_wo_overlap_in_time_steps")])
        iteration_results["dispatch_results"] = (
            iteration_results["dispatch_results"].append(
                sliced_dispatch_results))

        meta_results = processing.meta_results(self.om)
        # Objective is weighted in order to take overlap into account
        model_meta["overall_objective"] += (
            (int(meta_results["objective"]
                 * (getattr(self, "time_slice_length_wo_overlap_in_time_steps")
                    / getattr(self, "time_slice_length_with_overlap"))))
        )
        model_meta["overall_solution_time"] += meta_results["solver"]["Time"]
        pps = self.get_power_prices_from_duals().iloc[
              0:getattr(self, "time_slice_length_wo_overlap_in_time_steps")]
        iteration_results["power_prices"] = (
            iteration_results["power_prices"].append(pps)
        )

    def retrieve_initial_states_rolling_horizon(self, iteration_results):
        r"""Retrieve the initial states for the upcoming rolling horizon run

        Parameters
        ----------
        iteration_results : dict
            A dictionary holding the results of the previous rolling horizon
            iteration
        """
        iteration_results["storages_initial"] = pd.DataFrame(
            columns=["initial_storage_level_last_iteration"],
            index=getattr(self, "storage_labels"))

        for i, s in iteration_results["storages_initial"].iterrows():
            storage = views.node(iteration_results["model_results"], i)

            iteration_results["storages_initial"].at[
                i, "initial_storage_level_last_iteration"] = (
                storage["sequences"][((i, "None"),
                                      "storage_content")].iloc[
                    getattr(
                        self,
                        "time_slice_length_wo_overlap_in_time_steps") - 1])

        logging.info("Obtained initial (storage) levels for next iteration")
