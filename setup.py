#!/usr/bin/env python

# Note: To use the 'upload' functionality of this file, you must:
#   $ pipenv install twine --dev

import os

from setuptools import find_packages, setup

# Package meta-data.
NAME = "pikobrowser"
DESCRIPTION = "Piko browser."
URL = "https://github.com/Jaggler3/term"
EMAIL = "martin.protostar@gmail.com"
AUTHOR = "Martin Darazs"
REQUIRES_PYTHON = ">=3.6.0"
VERSION = "0.2.27"

# What packages are required for this module to be executed?
REQUIRED = ["requests", "simpleeval", "pyperclip", "art"]

EXTRAS = {}

# The rest you shouldn't have to touch too much :)
# ------------------------------------------------
# Except, perhaps the License and Trove Classifiers!
# If you do change the License, remember to change the Trove Classifier for that!

here = os.path.abspath(os.path.dirname(__file__))

# Where the magic happens:
setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    author=AUTHOR,
    author_email=EMAIL,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    packages=find_packages(exclude=["tests", "*.tests", "*.tests.*", "tests.*"]),
    scripts=["bin/piko"],
    install_requires=REQUIRED,
    extras_require=EXTRAS,
    include_package_data=True,
    license="MIT",
    classifiers=[
        # Trove classifiers
        # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
    ],
    entry_points={
        "console_scripts": ["piko=piko.app:main"],
    },
)
