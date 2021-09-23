# pommesdispatch

**A bottom-up fundamental power market model for the German electricity sector**

This is the **dispatch variant** of the fundamental power market model *POMMES* (**PO**wer **M**arket **M**odel of **E**nergy and re**S**ources).<br>
Please navigate to the section of interest to find out more.

## Contents
* [Introduction](#introduction)
* [Documentation](#documentation)
* [Installation](#installation)
    * [Setting up the environment](#setting-up-the-environment)
    * [Installing a solver](#installing-a-solver)
* [Contributing](#contributing)
* [Citing](#citing)
* [License](#license)

## Introduction
*POMMES* itself is a cosmos consisting of a **dispatch model** (stored in this repository and described here), a **data preparation routine** and an **investment model** for the German wholesale power market. The model was originally developed by a group of researchers and students at the [chair of Energy and Resources Management of TU Berlin](https://www.er.tu-berlin.de/menue/home/) and is now maintained by a group of alumni and open for other contributions.

If you are interested in the data preparation routines used or investment modeling, please find more information here:
- [pommesdata](https://github.com/pommes-public/pommesdata): A full-featured transparent data preparation routine from raw data to POMMES model inputs
- pommes-invest: A multi-period integrated investment and dispatch model for the German power sector (upcoming).

### Purpose and model characterization
The **dispatch variant** of the power market model *POMMES* `pommesdispatch` enables the user to simulate the **dispatch of backup power plants, storages as well as demand response units for the Federal Republic of Germany** for an arbitrary year or timeframe between 2017 and 2030. The dispatch of renewable power plants is exogeneously determined by normalized infeed time series and capacity values. The models' overall goal is to minimize power system costs occuring from wholesale markets whereby no network constraints are considered except for the existing bidding zone configuration used for modeling electricity exchange. Thus, the model purpose is to simulate **dispatch decisions** and the resulting **day-ahed market prices**. A brief categorization of the model is given in the following table. An extensive categorization can be found in the [model documentation]().

| **criterion** | **manifestation** |
| ---- | ---- |
| Purpose | - simulation of power plant dispatch and day-ahead prices for DE (scenario analysis) |
| Spatial coverage | - Germany (DE-LU) + electrical neighbours (NTC approach) |
| Time horizon | - usually 1 year in hourly resolution |
| Technologies | - conventional power plants, storages, demand response (optimized)<br> - renewable generators (fixed)<br> - demand: exogenous time series |
| Data sources | - OPSD, BNetzA, ENTSO-E, others (see [pommesdata](https://github.com/pommes-public/pommesdata)) |
| Implementation | - graph representation & linear optimization: oemof.solph / pyomo<br> - data management: python / .csv |

### Mathematical and technical implementation
The models' underlying mathematical method is a **linear programming** approach, seeking to minimize overall power system costs under constraints such as satisfying power demand at all times and not violating power generation capacity or storage limits. Thus, binary variables such as units' status, startups and shutdowns are not accounted for.

The model builds on the framework **[oemof.solph](https://github.com/oemof/oemof-solph)** which allows to model energy systems in a graph-based representation with the underlying mathematical constraints and objective function terms implemented in **[pyomo](https://pyomo.readthedocs.io/en/stable/)**. Some of the required oemof.solph features - such as demand response modeling - have been provided by the *POMMES* core developers which are also active in the oemof community. Users not familiar with oemof.solph may find further information in the [oemof.solph documentation](https://oemof-solph.readthedocs.io/en/latest/readme.html).

## Documentation
An extensive **[documentation of pommesdispatch]()** can be found on readthedocs. It contains a model categorization, some energy economic and technical background information as well as documentation of the model functions and classes. 

## Installation
To set up `pommesdispatch`, you have to set up a virtual environment (e.g. using conda) or add the required packages to your python installation. Additionally, you have to install a solver in order to solve the mathematical optimization problem.

### Setting up the environment
`pommesdispatch` is (to be) hosted on [PyPI](). To install it, please use the following command
```
pip install pommesdispatch
```

For now, you still have to clone the environment and copy the files locally by typing
```
git clone https://github.com/pommes-public/pommesdispatch.git
```
After cloning the repository, you have to install the required dependencies. Make sure you have conda installed as a package manager. If not, you can download it [here](https://www.anaconda.com/). Open a command shell and navigate to the folder where you copied the environment to. Use the following command to install dependencies
```
conda env create -f environment.yml
```
Activate your environment by typing
```
conda activate pommes_dispatch
```

### Installing a solver
In order to solve a `pommesdispatch` model instance, you need a solver installed. Please see [oemof.solph's information on solvers](https://github.com/oemof/oemof-solph#installing-a-solver). As a default, gurobi is used for `pommesdispatch` models. It is a commercial solver, but provides academic licenses, though, if this applies to you. Elsewhise, we recommend to use CBC as the solver oemof recommends. To test your solver and oemof.solph installation, again see information from [oemof.solph](https://github.com/oemof/oemof-solph#installation-test).

## Contributing
Every kind of contribution or feedback is warmly welcome.<br>
We use the GitHub issue management as well as pull requests for collaboration. We try to stick to the PEP8 coding standards.

## Citing
A publication using and introducing `pommesdispatch` is currently in preparation.

If you are using `pommesdispatch` for your own analyses, please cite as:<br>
*Kochems, J.; Werner, Y.; Giehl, J.; Grosse, B. et al. (2021): pommesdispatch. A bottom-up fundamental power market model for the German electricity sector. https://github.com/pommes-public/pommesdispatch, accessed YYYY-MM-DD.*

We furthermore recommend to name the version tag or the commit hash used for the sake of transparancy and reproducibility.

## License
This software is licensed under MIT License.

Copyright 2021 pommes developer group

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
