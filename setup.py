#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
setup

Setup for rafts_python package

Author: Jeffrey Glaister
"""
from glob import glob
from setuptools import setup, find_packages

args = dict(
    name='sct_pipeline',
    version='0.1',
    description="Central vein sign segmentation",
    author='Jeffrey Glaister',
    author_email='jeff.glaister@gmail.com',
    url='https://github.com/jglaister/sct_pipeline',
    keywords="central vein sign"
)

setup(install_requires=['nipype', 'rpy2', 'numpy', 'nibabel', 'scikit-image'],
      packages=['sct_pipeline'],
      scripts=glob('bin/*'), **args)

