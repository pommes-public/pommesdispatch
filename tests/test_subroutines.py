import numpy as np
import oemof.solph
import pandas as pd

from pommesdispatch.model_funcs import subroutines, model_control, data_input


def create_inputs_model_and_nodes():
    """Create and return input data, a dispatch model and a node dict"""
    dm = model_control.DispatchModel()
    dm.update_model_configuration(
        {"path_folder_input": "./csv_files/",
         "fuel_cost_pathway": "middle",
         "start_time": "2017-01-01 00:00:00",
         "end_time": "2017-01-02 00:00:00",
         "freq": "60min",
         "emissions_pathway": "100_percent_linear",
         "aggregate_input": False,
         "activate_demand_response": False},
        nolog=True
    )
    input_data = data_input.parse_input_data(dm)
    node_dict = {}

    return input_data, dm, node_dict


class TestSubroutines:
    """Test class for subroutines.py"""

    def test_load_input_data(self):
        """test function load_input_data"""
        csv_file = subroutines.load_input_data(
            filename="transformers_minload_ts_2017_w_nans",
            path_folder_input='./csv_files/',
            countries=["DE", "AT", "FR"])

        assert csv_file.columns.all() == pd.Index(
            ['chp', 'chp_natgas', 'chp_lignite',
             'chp_hardcoal', 'ipp', 'FR_natgas',
             'AT_natgas']).all()
        assert csv_file.index.all() == pd.Index(
            ['2017-01-01 00:00:00',
             '2017-01-01 01:00:00',
             '2017-01-01 02:00:00',
             '2017-01-01 03:00:00',
             '2017-01-01 04:00:00']).all()

    def test_create_buses(self):
        """test function create_buses"""
        input_data, dm, node_dict = create_inputs_model_and_nodes()
        node_dict = subroutines.create_buses(input_data, node_dict)

        assert len(node_dict) == 6
        for node in node_dict.values():
            assert type(node) == oemof.solph.Bus

    def test_create_linking_transformers(self):
        """test function create_linking_transformers"""
        input_data, dm, node_dict = create_inputs_model_and_nodes()
        node_dict = subroutines.create_buses(input_data, node_dict)
        node_dict = subroutines.create_linking_transformers(
            input_data, dm, node_dict)

        assert len(node_dict) == 7
        assert type(node_dict["DE_link_AT"]) == oemof.solph.Transformer
        assert node_dict["DE_link_AT"].conversion_factors[
                   (node_dict["DE_bus_el"],
                    node_dict["AT_bus_el"])].default == 0.95
        assert node_dict["DE_link_AT"].inputs[node_dict[
            "DE_bus_el"]].nominal_value == 100000
        assert node_dict["DE_link_AT"].inputs[node_dict[
            "DE_bus_el"]].max == []

    def test_create_commodity_sources(self):
        """test function create_commodity_sources"""
        input_data, dm, node_dict = create_inputs_model_and_nodes()
        node_dict = subroutines.create_buses(input_data, node_dict)
        node_dict = subroutines.create_commodity_sources(
            input_data, dm, node_dict)

        assert len(node_dict) == 10
        assert type(node_dict["DE_source_hardcoal"]) == oemof.solph.Source
        assert node_dict["DE_source_hardcoal"].outputs[
                   node_dict["DE_bus_hardcoal"]].variable_costs.default == (
                   17.853)

    def test_create_shortage_sources(self):
        """test function create_shortage_sources"""
        input_data, dm, node_dict = create_inputs_model_and_nodes()
        node_dict = subroutines.create_buses(input_data, node_dict)
        node_dict = subroutines.create_shortage_sources(
            input_data, node_dict)

        assert len(node_dict) == 7
        assert type(node_dict["DE_source_el_shortage"]) == oemof.solph.Source
        assert node_dict["DE_source_el_shortage"].outputs[
                   node_dict["DE_bus_el"]
               ].variable_costs.default == 160

    def test_create_renewables(self):
        """test function create_renewables"""
        input_data, dm, node_dict = create_inputs_model_and_nodes()
        node_dict = subroutines.create_buses(input_data, node_dict)
        node_dict = subroutines.create_renewables(
            input_data, dm, node_dict)

        assert len(node_dict) == 7
        assert type(node_dict["DE_source_biomassEEG"]) == oemof.solph.Source
        assert node_dict["DE_source_biomassEEG"].outputs[
                   node_dict["DE_bus_el"]
               ].variable_costs.default == 0
        assert len(node_dict["DE_source_biomassEEG"].outputs[
                       node_dict["DE_bus_el"]
                   ].fix) == 5
        assert node_dict["DE_source_biomassEEG"].outputs[
                   node_dict["DE_bus_el"]
               ].nominal_value == 7263.8

    def test_create_demand(self):
        """test function create_demand"""
        input_data, dm, node_dict = create_inputs_model_and_nodes()
        node_dict = subroutines.create_buses(input_data, node_dict)
        node_dict = subroutines.create_demand(
            input_data, dm, node_dict)

        assert len(node_dict) == 7
        assert type(node_dict["DE_sink_el_load"]) == oemof.solph.Sink
        assert node_dict["DE_sink_el_load"].inputs[
                   node_dict["DE_bus_el"]
               ].nominal_value == 79063
        assert len(node_dict["DE_sink_el_load"].inputs[
                       node_dict["DE_bus_el"]
                   ].fix) == 5

    def test_create_excess_sinks(self):
        """test function create_excess_sinks"""
        input_data, dm, node_dict = create_inputs_model_and_nodes()
        node_dict = subroutines.create_buses(input_data, node_dict)
        node_dict = subroutines.create_excess_sinks(
            input_data, node_dict)

        assert len(node_dict) == 7
        assert type(node_dict["DE_sink_el_excess"]) == oemof.solph.Sink
        keys = ["DE_bus_solarPV", "DE_bus_windonshore", "DE_bus_windoffshore"]
        for key in keys:
            assert (node_dict["DE_sink_el_excess"].inputs[node_dict[key]]
                    is not None)

    def test_create_transformers_conventional(self):
        """test function create_transformers_conventional"""
        input_data, dm, node_dict = create_inputs_model_and_nodes()
        node_dict = subroutines.create_buses(input_data, node_dict)
        node_dict = subroutines.create_transformers_conventional(
            input_data, dm, node_dict)

        assert len(node_dict) == 9

        # Check basic transformer attributes
        assert np.round(
            node_dict[
                "DE_transformer_hardcoal_BNA0019"].outputs[
                node_dict["DE_bus_el"]].nominal_value,
            4) == 227.8669
        assert np.round(
            node_dict[
                "DE_transformer_hardcoal_BNA0019"].conversion_factors[
                node_dict["DE_bus_el"]].default, 3) == 0.438
        assert node_dict[
                   "DE_transformer_hardcoal_BNA0019"].outputs[
                   node_dict["DE_bus_el"]].positive_gradient[
                   "ub"].default == 1.0

        # Check minimum loads for CHP unit
        assert len(node_dict[
                       "DE_transformer_hardcoal_BNA0019"].outputs[
                       node_dict["DE_bus_el"]].min) == 5
        assert node_dict[
                   "DE_transformer_hardcoal_BNA0019"].outputs[
                   node_dict["DE_bus_el"]].min.max() == 0.75

        # Check minimum loads for IPP unit
        assert len(node_dict[
                       "DE_transformer_hardcoal_BNA0216a"].outputs[
                       node_dict["DE_bus_el"]].min) == 5
        assert node_dict[
                   "DE_transformer_hardcoal_BNA0216a"].outputs[
                   node_dict["DE_bus_el"]].min.max() == 1.0

    def test_create_transformers_res(self):
        """test function create_transformers_res"""
        input_data, dm, node_dict = create_inputs_model_and_nodes()
        node_dict = subroutines.create_buses(input_data, node_dict)
        node_dict = subroutines.create_transformers_res(
            input_data, dm, node_dict)

        assert len(node_dict) == 12
        assert np.round(
            node_dict[
                "DE_solarPV_cluster_1"].outputs[
                node_dict["DE_bus_el"]].nominal_value,
            4) == 309.13
        assert len(
            node_dict[
                "DE_solarPV_cluster_1"].outputs[
                node_dict["DE_bus_el"]].variable_costs) == 5
        assert np.round(node_dict[
                            "DE_windonshore_cluster_1"].outputs[
                            node_dict["DE_bus_el"]].max.max(), 4) == 0.2479

    def test_create_storages(self):
        """test function create_storages"""
        input_data, dm, node_dict = create_inputs_model_and_nodes()
        node_dict = subroutines.create_buses(input_data, node_dict)
        node_dict = subroutines.create_storages(
            input_data, dm, node_dict)

        assert len(node_dict) == 7
        assert node_dict["DE_storage_el_PHS"].balanced is True
        assert node_dict["DE_storage_el_PHS"].initial_storage_level == 0.5
        assert np.round(
            node_dict["DE_storage_el_PHS"].nominal_storage_capacity,
            1) == 25116.0
        assert np.round(
            node_dict["DE_storage_el_PHS"].inputs[
                node_dict["DE_bus_el"]].nominal_value, 2) == 8680.75
        assert np.round(
            node_dict["DE_storage_el_PHS"].outputs[
                node_dict["DE_bus_el"]].nominal_value, 2) == 4475.25
        assert np.round(
            node_dict["DE_storage_el_PHS"].inflow_conversion_factor.default,
            1) == 0.9

    def test_create_storages_rolling_horizon(self):
        """test function create_storages_rolling_horizon"""
        input_data, dm, node_dict = create_inputs_model_and_nodes()
        node_dict = subroutines.create_buses(input_data, node_dict)
        iteration_results = {
            "storages_initial": pd.DataFrame(),
            "model_results": {},
            "dispatch_results": pd.DataFrame(),
            "power_prices": pd.DataFrame()
        }
        node_dict, storage_labels = (
            subroutines.create_storages_rolling_horizon(
                input_data, dm, node_dict, iteration_results))

        assert len(node_dict) == 7
        assert node_dict["DE_storage_el_PHS"].balanced is True
        assert node_dict["DE_storage_el_PHS"].initial_storage_level == 0.5
        assert np.round(
            node_dict["DE_storage_el_PHS"].nominal_storage_capacity,
            1) == 25116.0
        assert np.round(
            node_dict["DE_storage_el_PHS"].inputs[
                node_dict["DE_bus_el"]].nominal_value, 2) == 8680.75
        assert np.round(
            node_dict["DE_storage_el_PHS"].outputs[
                node_dict["DE_bus_el"]].nominal_value, 2) == 4475.25
        assert np.round(
            node_dict["DE_storage_el_PHS"].inflow_conversion_factor.default,
            1) == 0.9
