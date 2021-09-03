from pommes_dispatch.model.dispatch_model import run_dispatch_model, add_args


def run_pommes_dispatch():
    config_yml = add_args()
    run_dispatch_model(config_yml)
