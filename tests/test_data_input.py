import oemof.solph
import pandas as pd

from pommesdispatch.model_funcs import data_input, model_control


def create_dispatch_model():
    """Create a dispatch model and attribute it with some information"""
    dm = model_control.DispatchModel()
    dm.update_model_configuration(
        {
            "path_folder_input": "tests/csv_files/",
            "fuel_cost_pathway": "NZE",
            "fuel_price_shock": "high",
            "emissions_cost_pathway": "long-term",
            "start_time": "2017-01-01 00:00:00",
            "end_time": "2017-01-02 00:00:00",
            "freq": "60min",
            "emissions_pathway": "100_percent_linear",
            "aggregate_input": False,
            "activate_demand_response": False,
        },
        nolog=True,
    )

    return dm


def return_node_labels_and_dtypes():
    """Return labels and dtypes (except for storages units)"""
    nodes_dict_keys = [
        "DE_bus_el",
        "DE_bus_hardcoal",
        "DE_bus_solarPV",
        "DE_bus_windonshore",
        "DE_bus_windoffshore",
        "AT_bus_el",
        "DE_link_AT",
        "DE_source_hardcoal",
        "DE_source_solarPV",
        "DE_source_windoffshore",
        "DE_source_windonshore",
        "DE_source_el_shortage",
        "DE_source_el_shortage_add_0",
        "DE_source_el_shortage_add_1",
        "DE_source_biomassEEG",
        "DE_sink_el_load",
        "DE_sink_el_excess",
        "DE_transformer_hardcoal_BNA0019",
        "DE_transformer_hardcoal_BNA0147",
        "DE_transformer_hardcoal_BNA0216a",
        "DE_solarPV_cluster_1",
        "DE_solarPV_cluster_2",
        "DE_windonshore_cluster_1",
        "DE_windonshore_cluster_2",
        "DE_windoffshore_cluster_1",
        "DE_windoffshore_cluster_2",
    ]
    nodes_dict_dtypes = [
        oemof.solph.Source,
        oemof.solph.Sink,
        oemof.solph.Bus,
        oemof.solph.Transformer,
    ]

    return nodes_dict_keys, nodes_dict_dtypes


class TestDataInput:
    """Test class for data_input.py"""

    def test_parse_input_data(self):
        """test function parse_input_data"""
        dm = create_dispatch_model()
        input_data = data_input.parse_input_data(dm)
        assert len(input_data.keys()) == 31
        input_data_keys = [
            "linking_transformers",
            "sinks_excess",
            "sinks_demand_el",
            "sources_shortage",
            "sources_shortage_el_add",
            "sources_renewables_fluc",
            "sources_commodity",
            "sources_renewables",
            "storages_el",
            "transformers",
            "transformers_renewables",
            "linking_transformers_ts",
            "sinks_demand_el_ts",
            "costs_market_values",
            "sources_renewables_ts",
            "transformers_minload_ts",
            "transformers_availability_ts",
            "costs_fuel",
            "costs_fuel_ts",
            "costs_emissions",
            "costs_emissions_ts",
            "costs_operation",
            "costs_operation_renewables",
            "costs_operation_storages",
            "min_loads_dh",
            "min_loads_ipp",
            "dh_gradients_ts",
            "ipp_gradients_ts",
            "remaining_gradients_ts",
        ]

        for el in input_data_keys:
            assert el in input_data.keys()

    def test_add_components(self):
        """Test function add_components"""
        dm = create_dispatch_model()
        input_data = data_input.parse_input_data(dm)
        nodes_dict = data_input.add_components(input_data, dm)
        nodes_dict_keys, nodes_dict_dtypes = return_node_labels_and_dtypes()

        for key, value in nodes_dict.items():
            assert key in nodes_dict_keys
            assert type(value) in nodes_dict_dtypes

    def test_add_limits(self):
        """Test function add_limits for adding an emissions limit"""
        dm = create_dispatch_model()
        input_data = data_input.parse_input_data(dm)
        emissions_limit = data_input.add_limits(
            input_data, dm.emissions_pathway, dm.start_time, dm.end_time
        )

        assert round(emissions_limit) == 853425

    def test_nodes_from_csv(self):
        """Test function nodes_from_csv"""
        dm = create_dispatch_model()
        nodes_dict, emissions_limit = data_input.nodes_from_csv(dm)
        nodes_dict_keys, nodes_dict_dtypes = return_node_labels_and_dtypes()
        nodes_dict_keys.append("DE_storage_el_PHS")
        nodes_dict_dtypes.append(oemof.solph.GenericStorage)

        assert emissions_limit is None
        for key, value in nodes_dict.items():
            assert key in nodes_dict_keys
            assert type(value) in nodes_dict_dtypes

    def test_nodes_from_csv_rh(self):
        """Test function nodes_from_csv_rh"""
        dm = create_dispatch_model()
        iteration_results = {
            "storages_initial": pd.DataFrame(),
            "model_results": {},
            "dispatch_results": pd.DataFrame(),
            "power_prices": pd.DataFrame(),
        }
        dm.add_rolling_horizon_configuration(
            rolling_horizon_parameters={
                "time_slice_length_wo_overlap_in_hours": 24,
                "overlap_in_hours": 12,
            },
            nolog=True,
        )

        (
            nodes_dict,
            emissions_limit,
            storage_labels,
        ) = data_input.nodes_from_csv_rh(dm, iteration_results)
        nodes_dict_keys, nodes_dict_dtypes = return_node_labels_and_dtypes()
        nodes_dict_keys.append("DE_storage_el_PHS")
        nodes_dict_dtypes.append(oemof.solph.GenericStorage)

        assert storage_labels == ["DE_storage_el_PHS"]
        assert emissions_limit is None
        for key, value in nodes_dict.items():
            assert key in nodes_dict_keys
            assert type(value) in nodes_dict_dtypes
