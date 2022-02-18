from pommesdispatch.model.dispatch_model import run_dispatch_model, add_args


def create_default_config():
    content = """# Determine the model configuration

# 1) Set overall workflow control parameters
control_parameters:
    rolling_horizon: False
    aggregate_input: False
    countries: ['AT', 'BE', 'CH', 'CZ', 'DE', 'DK1', 'DK2', 'FR', 'NL',
                'NO1', 'NO2', 'NO3', 'NO4', 'NO5', 'PL',
                'SE1', 'SE2', 'SE3', 'SE4']
    solver: "gurobi"
    fuel_cost_pathway: "middle"
    activate_emissions_limit: False
    emissions_pathway: "100_percent_linear"
    activate_demand_response: False
    demand_response_approach: "DLR"
    demand_response_scenario: "50"
    save_production_results: True
    save_price_results: True
    write_lp_file: False

# 2) Set model optimization time and frequency
time_parameters:
    start_time: "2017-01-01 00:00:00"
    end_time: "2017-01-02 23:00:00"
    freq: "60min"

# 3) Set input and output data paths
input_output_parameters:
    path_folder_input: "./inputs/"
    path_folder_output: "./results/"

# 4) Set rolling horizon parameters (optional)
rolling_horizon_parameters:
    time_slice_length_wo_overlap_in_hours: 24
    overlap_in_hours: 12"""
    with open("./config.yml", "w") as opf:
        opf.write(content)


def run_pommes_dispatch():
    args = add_args()
    if args.init:
        create_default_config()
        return
    # Use multiple iterations to update market values
    if args.iterations > 1:
        print(
            f"Running pommesdispatch ITERATIVELY in "
            f"{args.iterations} iterations"
        )
        for iteration in range(args.iterations):
            print(f"STARTING ITERATION {iteration}")
            run_dispatch_model(args.file)
            print(f"ITERATION {iteration} completed")
            print("-" * 60)
    else:
        run_dispatch_model()


if __name__ == "__main__":
    run_pommes_dispatch()
