# -*- coding: utf-8 -*-
"""
General description
------------------
This file contains all function definitions for controlling the model
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

from pommes_dispatch.model_funcs import helpers
from .data_input import nodes_from_csv, nodes_from_csv_rh


class DispatchModel():
    """A class that holds an dispatch model.

    A dispatch model is a container for all the model parameters as well
    as for methods for controlling the model workflow.

    Parameters
    ----------


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

    demand_response_scenario : :obj:`str`
        Demand response scenario to be modeled;
        must be one of ['25', '50', '75'] whereby '25' is the lower,
        i.e. rather pessimistic estimate

    path_folder_input : :obj:`str`
        The path_folder_output where the input data is stored
    """

    def __init__(self):
        """Initialize an empty DispatchModel object"""
        self.rolling_horizon = None
        self.aggregate_input = None
        self.countries = None
        self.solver = None
        self.fuel_cost_pathway = None
        self.activate_emissions_limit =None
        self.emission_pathway = None
        self.activate_demand_response = None
        self.demand_response_approach = None
        self.demand_response_scenario = None
        self.save_production_results = None
        self.save_price_results = None
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
            Show no logging ingo if True
        """
        for param_dict in model_parameters:
            for k, v in param_dict.items():
                if not nolog:
                    if hasattr(self, k):
                        logger.info(
                            f"Updating attribute `{k}` with value '{v}'.")
                    else:
                        logger.info(
                            f"Adding attribute `{k}` with value '{v}' "
                            + "to the model.")
                setattr(self, k, v)

        if hasattr(self, "start_time"):
            setattr(self, "year", str(pd.to_datetime(self.start_time).year))

    def check_model_configuration(self):
        """Checks if any necessary model parameter hasn't been set yet"""
        for entry in dir(self):
            if not entry.startswith("_"):
                if entry != "om" and getattr(self, entry) is None:
                    logging.warning(
                        f"Necessary model parameter `{entry}` "
                        + "has not yet been specified!")

    def add_rh_configuration(self, RH_parameters):
        """Add a rolling horizon configuration to the dispatch model"""
        self.update_model_configuration(RH_parameters)

        setattr(self, "time_series_start",
                pd.Timestamp(self.start_time, self.freq))
        setattr(self, "time_series_end",
                pd.Timestamp(self.end_time, self.freq))
        setattr(self, "time_slice_length_wo_overlap_in_timesteps",
                ({'60min': 1, '15min': 4}[self.freq]
                 * self.time_slice_length_wo_overlap_in_hours))
        setattr(self, "overlap_in_time_steps",
                ({'60min': 1, '15min': 4}[self.freq]
                 * self.overlap_in_hours))
        setattr(self, "time_slice_length_with_overlap",
                (getattr(self, "time_slice_length_wo_overlap_in_time_steps")
                + getattr(self, "overlap_in_time_steps")))
        setattr(self, "overall_timesteps",
                helpers.time_steps_between_timestamps(
                    self.time_series_start, self.time_series_end, self.freq))
        setattr(self, "amount_of_timeslices",
                math.ceil(self.overall_time_steps
                          / self.time_slice_length_wo_overlap_in_time_steps))

    def initialize_logging(self):
        """Initialize logging by deriving a filename from the configuration"""
        optimization_timeframe = helpers.days_between(self.start_time,
                                                      self.end_time)

        if not self.rolling_horizon:
            rh = 'simple_'
        else:
            rh = 'RH_'
        if self.aggregate_input:
            agg = 'clustered_'
        else:
            agg = 'complete_'

        filename = ("dispatch_LP_" + "start-" + self.start_time[:10] + "_"
                    + str(optimization_timeframe) + "-days_" + rh + agg)

        setattr(self, "filename", filename)
        logger.define_logging(logfile=filename + ".log")

    def show_configuration_log(self):
        """Show some logging info dependent on model configuration"""
        if self.aggregate_input:
            logging.info("Using the AGGREGATED POWER PLANT DATA SET")
        else:
            logging.info("Using the COMPLETE POWER PLANT DATA SET.\n"
                         "Minimum power output constraint of (individual)\n"
                         "transformers will be neglected.")

        if self.activate_demand_response:
            logging.info(
                f"Using approach from {self.demand_response_approach}"
                f"for DEMAND RESPONSE modeling\n"
                f"Considering a {self.demand_response_scenario}% scenario")
        else:
            logging.info("Running a model WITHOUT DEMAND RESPONSE")

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

    def initial_states_RH(
            self,
            model_results,
            timeslice_length_wo_overlap_in_timesteps,
            storage_labels):
        r"""Obtain the initial states for the upcoming rolling horizon model run.

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

    def build_RH_model(
            self,
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
            year,
            activate_emissions_limit,
            emission_pathway,
            activate_demand_response,
            approach,
            scenario):
        r"""Set up and return a rolling horizon LP dispatch model

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
            activate_emissions_limit,
            emission_pathway,
            activate_demand_response,
            approach,
            scenario)

        # Update for next iteration
        timeseries_start = timeseries_end

        es.add(*node_dict.values())
        logging.info(
            f"Sucessfully set up energy system for iteration {counter}")

        om = models.Model(es)

        add_further_constrs(
            om,
            activate_emissions_limit,
            emissions_limit)

        return om, es, timeseries_start, storage_labels, datetime_index

    def solve_RH_model(
            self,
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
        logging.info(
            'Obtaining dual values and reduced costs from the model \n'
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
            om, datetime_index).iloc[
              0:timeslice_length_wo_overlap_in_timesteps]
        power_prices = power_prices.append(pps)

        return (om, model_results, results, overall_objective,
                overall_solution_time, power_prices)

    def show_meta_logging_info(self, model_meta):
        """Show some logging information on model meta data"""
        logging.info(f"***** MODEL RUN TERMINATED SUCESSFULLY :-) *****")
        logging.info(f"Overall objective value: "
                     + f"{model_meta['overall_objective']:.2f}")
        logging.info(f"Overall solution time: "
                     + f"{model_meta['overall_solution_time']:.2f}")
        logging.info(f"Overall time: "
                     +
                     f"{model_meta['overall_time']:.2f}")
