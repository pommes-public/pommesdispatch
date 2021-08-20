# pommes-dispatch

**A bottom-up fundamental power market model for the German electricity sector**

This is the **dispatch variant** of the fundamental power market model *POMMES* (**PO**wer **M**arket **M**odel of **E**nergy and re**S**ources).<br>
Please navigate to the section of interest to find out more.

## Contents
* Introduction
* Documentation
* Installation
    * Setting up the environment
    * Installing a solver
* Contributing
* Citing
* License

## Introduction
*POMMES* itself is a cosmos consisting of a dispatch model (stored in this repository and described here), a data preparation routine and an investment model for the German wholesale power market.

If you are interested in the data preparation routines used or investment modeling, please find more information here:
- [pommes-data](https://github.com/pommes-public/pommes-data): A full-featured transparent data preparation routine from raw data to POMMES model inputs
- pommes-invest: A multi-period integrated investment and dispatch model for the German power sector (upcoming).

### Purpose and model characterization
The **dispatch variant** of the power market model *POMMES* enables the user to simulate the **dispatch of backup power plants, storages as well as demand response units for the Federal Republic of Germany** for an arbitrary year or timeframe between 2017 and 2030. The dispatch of renewable power plants is exogeneously determined by normalized infeed time series and capacity values. The models' overall goal is to minimize power system costs occuring from wholesale markets whereby no network constraints are considered except for the existing bidding zone configuration. Thus, the model purpose is to simulate dispatch decisions and the resulting day-ahed market prices. Since it largely influences power prices and dispatch decisions, the exchange with the electrical neighbouring countries of Germany is simulated as well. A brief categorization of the model according to Hall and Buckley (2016) is given in the following table.

<Categorization>

### Mathematical and technical implementation
The models' underlying mathematical method is a **linear programming** approach, seeking to minimize overall power system costs under constraints such as satisfying power demand at all times and not violating power generation capacity or storage limits. Thus, binary variables such as units' status, startups and shutdowns are not accounted for.

The model builds on the framework oemof.solph which allows to model energy systems in a graph-based representation with the underlying mathematical constraints and objective function terms implemented in pyomo. Some of the required oemof.solph features - such as demand response modeling - have been provided by the *POMMES* core developers which are also active in the oemof community. Users not familiar with oemof.solph may find further information in its [documentation](https://oemof-solph.readthedocs.io/en/latest/readme.html).

## Documentation

## Installation
### Setting up the environment
### Installing a solver

## Contributing

## Citing

## License
