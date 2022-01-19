#! /usr/bin/env python3
from setuptools import setup
from setuptools import find_packages

from docs import get_version


CHANGELOG = open('CHANGES.rst').read()
LONG_DESCRIPTION = "\n\n".join([
    open('README.rst').read(),
    CHANGELOG
])


setup(
    name='DHTMLParser3',
    version=get_version(CHANGELOG),
    py_modules=['dhtmlparser3'],

    author='Bystroushaak',
    author_email='bystrousak@kitakitsune.org',

    url='https://github.com/Bystroushaak/DHTMLParser3',
    license='MIT',
    description='Python HTML/XML parser for easy web scraping.',

    long_description=LONG_DESCRIPTION,

    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,

    classifiers=[
        "License :: OSI Approved :: MIT License",

        "Programming Language :: Python",
        "Programming Language :: Python :: 3",

        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",

        "Topic :: Text Processing :: Markup :: HTML",
        "Topic :: Text Processing :: Markup :: XML"
    ],

    extras_require={
        "test": [
            "pytest",
            "pytest-cov",
        ],
        "docs": [
            "sphinx",
            "sphinxcontrib-napoleon",
        ]
    }
)
