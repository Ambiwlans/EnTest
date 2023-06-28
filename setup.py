# -*- coding: utf-8 -*-
"""
@author: Ambiwlans
@general: EnTest - English Vocab testing site
@description: Setup for installing the site as a package
"""

from setuptools import setup, find_packages

setup(
    name='EnTest',
    packages=['EnTest'],
    #long_description=__doc__,
    include_package_data=True,
    zip_safe=False,
    install_requires=find_packages(),
)