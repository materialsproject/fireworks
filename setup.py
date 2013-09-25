#!/usr/bin/env python

__author__ = "Anubhav Jain"
__copyright__ = "Copyright 2013, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Anubhav Jain"
__email__ = "ajain@lbl.gov"
__date__ = "Jan 9, 2013"

from setuptools import setup, find_packages
from fireworks import __version__
import os
import multiprocessing, logging  # AJ: for some reason this is needed to not have "python setup.py test" freak out

module_dir = os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
    setup(name='FireWorks',
          version=__version__,
          description='FireWorks workflow software',
          long_description=open(os.path.join(module_dir, 'README.rst')).read(),
          url='https://github.com/materialsproject/fireworks',
          author='Anubhav Jain',
          author_email='anubhavster@gmail.com',
          license='modified BSD',
          packages=find_packages(),
          zip_safe=False,
          install_requires=['pyyaml>=3.1.0', 'pymongo>=2.4.2', 'Jinja2>=2.7.1'],
          extras_require={'rtransfer': ['paramiko>=1.11']},
          classifiers=['Programming Language :: Python :: 2.7', 'Development Status :: 4 - Beta',
                       'Intended Audience :: Science/Research', 'Intended Audience :: System Administrators',
                       'Intended Audience :: Information Technology',
                       'Operating System :: OS Independent', 'Topic :: Other/Nonlisted Topic',
                       'Topic :: Scientific/Engineering'],
          test_suite='nose.collector',
          tests_require=['nose'],
          scripts=[os.path.join(os.path.join(module_dir, 'scripts', f)) for f in
                   os.listdir(os.path.join(module_dir, 'scripts'))])
