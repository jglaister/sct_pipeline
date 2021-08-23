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
    description="Spinalcordtoolbox segmentation",
    author='Jeffrey Glaister',
    author_email='jeff.glaister@gmail.com',
    url='https://github.com/jglaister/sct_pipeline'
)

setup(install_requires=['nipype', 'numpy', 'nibabel'],
      packages=['sct_pipeline.interfaces', 'sct_pipeline.workflows'],
      scripts=glob('bin/*'), **args)

