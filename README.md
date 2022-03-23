![PyPI](https://img.shields.io/pypi/v/pommesdispatch)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pommesdispatch)
![Documentation Status](https://readthedocs.org/projects/pommesdispatch/badge/?version=latest)
![PyPI - License](https://img.shields.io/pypi/l/pommesdispatch)
[![Coverage Status](https://coveralls.io/repos/github/pommes-public/pommesdispatch/badge.svg?branch=set-up-ci)](https://coveralls.io/github/pommes-public/pommesdispatch?branch=set-up-ci)

# pommesdispatch

**A bottom-up fundamental power market model for the German electricity sector**

This is the **dispatch variant** of the fundamental power market model *POMMES* (**PO**wer **M**arket **M**odel of **E**nergy and re**S**ources).
Please navigate to the section of interest to find out more.

## Contents
* [Introduction](#introduction)
* [Documentation](#documentation)
* [Installation](#installation)
    * [Setting up pommesdispatch](#setting-up-pommesdispatch)
    * [Installing a solver](#installing-a-solver)
* [Contributing](#contributing)
* [Citing](#citing)
* [License](#license)

## Introduction
*POMMES* itself is a cosmos consisting of a **dispatch model** (stored in this repository and described here), a **data preparation routine** and an **investment model** for the German wholesale power market. The model was originally developed by a group of researchers and students at the [chair of Energy and Resources Management of TU Berlin](https://www.er.tu-berlin.de/menue/home/) and is now maintained by a group of alumni and open for other contributions.

If you are interested in the data preparation routines used or investment modeling, please find more information here:
- [pommesdata](https://github.com/pommes-public/pommesdata): A full-featured transparent data preparation routine from raw data to POMMES model inputs
- pommesinvest: A multi-period integrated investment and dispatch model for the German power sector (upcoming).

### Purpose and model characterization
The **dispatch variant** of the power market model *POMMES* `pommesdispatch` enables the user to simulate the **dispatch of backup power plants, storages as well as demand response units for the Federal Republic of Germany** for an arbitrary year or timeframe between 2017 and 2030. The dispatch of renewable power plants is exogeneously determined by normalized infeed time series and capacity values. The models' overall goal is to minimize power system costs occuring from wholesale markets whereby no network constraints are considered except for the existing bidding zone configuration used for modeling electricity exchange. Thus, the model purpose is to simulate **dispatch decisions** and the resulting **day-ahed market prices**. A brief categorization of the model is given in the following table. An extensive categorization can be found in the [model documentation]().

| **criterion** | **manifestation** |
| ---- | ---- |
| Purpose | - simulation of power plant dispatch and day-ahead prices for DE (scenario analysis) |
| Spatial coverage | - Germany (DE-LU) + electrical neighbours (NTC approach) |
| Time horizon | - usually 1 year in hourly resolution |
| Technologies | - conventional power plants, storages, demand response (optimized)<br> - renewable generators (fixed)<br> - demand: exogenous time series |
| Data sources | - input data not shipped out, but can be obtained from [pommesdata](https://github.com/pommes-public/pommesdata); OPSD, BNetzA, ENTSO-E, others |
| Implementation | - graph representation & linear optimization: [oemof.solph](https://github.com/oemof/oemof-solph) / [pyomo](https://github.com/Pyomo/pyomo) <br> - data management: python / .csv |

### Mathematical and technical implementation
The models' underlying mathematical method is a **linear programming** approach, seeking to minimize overall 
power system costs under constraints such as satisfying power demand at all times and not violating power generation 
capacity or storage limits. Thus, binary variables such as units' status, startups and shutdowns are not accounted for.

The model builds on the framework **[oemof.solph](https://github.com/oemof/oemof-solph)** which allows modeling
energy systems in a graph-based representation with the underlying mathematical constraints and objective function 
terms implemented in **[pyomo](https://pyomo.readthedocs.io/en/stable/)**. Some of the required oemof.solph featuresm - such as demand response modeling - have been provided by the *POMMES* main developers which are also active in the 
oemof community. Users not familiar with oemof.solph may find further information in the 
[oemof.solph documentation](https://oemof-solph.readthedocs.io/en/latest/readme.html).

## Documentation
An extensive **[documentation of pommesdispatch](https://pommesdispatch.readthedocs.io/)** can be found on readthedocs. It contains a user's guide, a model categorization, some energy economic and technical background information, a complete model formulation as well as documentation of the model functions and classes. 

## Installation
To set up `pommesdispatch`, set up a virtual environment (e.g. using conda) or add the required packages to your python installation. Additionally, you have to install a solver in order to solve the mathematical optimization problem.

### Setting up pommesdispatch
`pommesdispatch` is hosted on [PyPI](https://pypi.org/project/pommesdispatch/). 
To install it, please use the following command
```
pip install pommesdispatch
```

If you want to contribute as a developer, you fist have to
[fork](https://docs.github.com/en/get-started/quickstart/fork-a-repo>)
it and then clone the repository, in order to copy the files locally by typing
```
git clone https://github.com/your-github-username/pommesdispatch.git
```
After cloning the repository, you have to install the required dependencies.
Make sure you have conda installed as a package manager.
If not, you can download it [here](https://www.anaconda.com/).
Open a command shell and navigate to the folder
where you copied the environment to.

Use the following command to install dependencies
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
We use the [GitHub issue management](https://github.com/pommes-public/pommesdispatch/issues) as well as 
[pull requests](https://github.com/pommes-public/pommesdispatch/pulls) for collaboration. We try to stick to the PEP8 coding standards.

The following people have contributed in the following manner to `pommesdispatch`:

| Name | Contribution | Status |
| ---- | ---- | ---- |
| Johannes Kochems | major development & conceptualization<br>conceptualization, core functionality (esp. dispatch, power prices, demand response, rolling horizon modeling), architecture, publishing process | coordinator & maintainer,<br>developer & corresponding author |
| Yannick Werner | major development & conceptualization<br>conceptualization, core functionality (esp. exchange, RES, CHP modeling), interface to pommesdata  | developer & corresponding author |
| Johannes Giehl | development<br>early-stage core functionality | developer |
| Benjamin Grosse | development<br>support for conceptualization, early-stage contributions at the interface to pommesdata | developer |
| Sophie Westphal | development<br>early-stage contributions at the interface to pommesdata | former developer (student assistant) |
| Flora von Mikulicz-Radecki | testing<br>early-stage comprehensive testing | former tester (student assistant) |
| Carla Spiller | development<br>early-stage rolling horizon and cross-border exchange integration | former developer (student assistant) |
| Fabian Büllesbach | development<br>early-stage rolling horizon implementation | former developer (master's student) |
| Timona Ghosh | development<br>early-stage cross-border exchange implementation | former developer (master's student) |
| Paul Verwiebe | support<br>support of early-stage core functionality development | former supporter (research associate) |
| Leticia Encinas Rosa | support<br>support of early-stage core functionality development | former supporter (research associate) |
| Joachim Müller-Kirchenbauer | support & conceptualization<br>early-stage conceptualization, funding | supporter (university professor) |

*Note: Not every single contribution is reflected in the current version of
`pommesdispatch`. This is especially true for those marked as early-stage 
contributions that may have been extended, altered or sometimes discarded. 
Nonetheless, all people listed have made valuable contributions. The ones
discarded might be re-integrated at some point in time.
Dedicated contributions to `pommesdata` and `pommesinvest` are not included
in the list, but listed individually for these projects.*

## Citing
A publication using and introducing `pommesdispatch` is currently in preparation.

If you are using `pommesdispatch` for your own analyses, we recommend citing as:<br>
*Kochems, J.; Werner, Y.; Giehl, J.; Grosse, B. et al. (2021): pommesdispatch. A bottom-up fundamental power market model for the German electricity sector. https://github.com/pommes-public/pommesdispatch, accessed YYYY-MM-DD.*

We furthermore recommend naming the version tag or the commit hash used for the sake of transparency and reproducibility.

Also see the *CITATION.cff* file for citation information.

## License
This software is licensed under MIT License.

Copyright 2021 pommes developer group

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
