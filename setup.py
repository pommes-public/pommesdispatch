from setuptools import setup, find_packages

__author__ = ["Johannes Kochems", "Yannick Werner",
              "Johannes Giehl", "Benjamin Grosse"]
__copyright__ = "Copyright 2021 pommes developer group"
__credits__ = ["Sophie Westphal", "Flora von Mikulicz-Radecki",
               "Carla Spiller", "Fabian Büllesbach", "Timona Ghosh",
               "Paul Verwiebe", "Leticia Encinas Rosa",
               "Joachim Müller-Kirchenbauer"]

__license__ = "MIT"
__maintainer__ = "Johannes Kochems"
__email__ = "jokochems@web.de"
__status__ = "Production"


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()


setup(
    name='pommes_dispatch',
    version='0.0.2',
    description='A bottom-up fundamental power market model '
                'for the German electricity sector',
    long_description=long_description,
    keywords=['power market', 'fundamental model', 'dispatch', 'power price',
              'Germany', 'oemof', 'oemof.solph', 'pyomo'],
    url='https://github.com/pommes-public/pommes_dispatch/',
    author=', '.join(__author__),
    author_email=__email__,
    license=__license__,
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    entry_points={
        'console_scripts': [
            'run_pommes_dispatch=pommes_dispatch.model:run_pommes_dispatch'
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    project_urls={
        "Documentation": "https://pommes_dispatch.readthedocs.io/",
        "Changelog": (
            "https://pommes_dispatch.readthedocs.io/en/latest/changelog.html"
        ),
        "Issue Tracker":
            "https://github.com/pommes-public/pommes_dispatch/issues",
    },
    install_requires=[
        'numpy',
        'pandas',
        'matplotlib',
        'oemof.solph == 0.4.4',
        'pyyaml'
    ],
    python_requires='>=3.7',
    extras_require={'test': ['pytest', 'sphinx', 'sphinx_rtd_theme']},
    include_package_data=True,
    zip_safe=False,
)
