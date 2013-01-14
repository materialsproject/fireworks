#!/usr/bin/env python

__author__ = "Anubhav Jain"
__copyright__ = "Copyright 2013, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Anubhav Jain"
__email__ = "ajain@lbl.gov"
__date__ = "Jan 9, 2013"

from setuptools import setup, find_packages


def readme():
    with open('README.txt') as f:
        return f.read()
    
setup(name='FireWorks',
      version='0.1dev0.5',
      description='FireWorks workflow software',
      long_description=open('README.txt').read(),
      
      # TODO: PyPI link?
      url='https://github.com/materialsproject/fireworks',
      author='Anubhav Jain',
      author_email='anubhavster@gmail.com',
      license='MIT',
      packages=find_packages(),
      zip_safe=False,
      install_requires=['pyyaml'],
      classifiers=[
        "Programming Language :: Python :: 2.7",
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Science/Research",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Other/Nonlisted Topic",
        "Topic :: Scientific/Engineering"],
        test_suite='nose.collector',
        tests_require=['nose']
        )
