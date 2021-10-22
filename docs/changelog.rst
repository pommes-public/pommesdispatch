Changelog
=========

v0.1.0 (2021-10-21)
-------------------

Initial public release of ``pommesdispatch`` available on PyPI

* Fixed architecture and docs
* Made input data dependent on years / flexible for years from ``pommesdata`` (2017 until 2030)
* Introduced console scripts for configuring and running
* Added poetry build
* Added tests (with coverage of 88%)
* Added linting CI
* Included CITATION.cff
* Used version numbering convention

v0.0.2 (2021-09-03)
-------------------

* Added a draft sphinx documentation
* Allowed configuring of model via yaml
* introduced console script

v0.0.1 (2021-08-05)
-------------------

Initial release of ``pommesdispatch``

Welcome to the *POMMES* cosmos!

**A bottom-up fundamental power market model for the German electricity sector**

Features:

* ``pommesdispatch`` is the **dispatch** variant of *POMMES* that allows
  to simulate dispatch decisions and power prices for Germany
  in hourly resolution for one year (or shorter time frames).
* ``pommesdispatch`` allows for negative power prices
  due to its in-depth representation of renewable plants in the market premium scheme.
* Consistent input data sets for *POMMES* models can be obtained from
  `pommesdata <https://github.com/pommes-public/pommesdata>`_,
  supporting years between 2017 and 2030 and taking into account various open data sources.
* All *POMMES* models are easy to adjust and extend
  because it is build on top of `oemof.solph <https://github.com/oemof/oemof-solph>`_.

Stay tuned for upcoming releases as well as the **data preparation** package ``pommesdata`` and the **investment** variant ``pommes-invest``!
