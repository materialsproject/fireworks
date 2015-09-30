#!/usr/bin/env python

__author__ = "Anubhav Jain"
__copyright__ = "Copyright 2013, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Anubhav Jain"
__email__ = "ajain@lbl.gov"
__date__ = "Jan 9, 2013"

from setuptools import setup, find_packages
import os
import multiprocessing, logging  # AJ: for some reason this is needed to not have "python setup.py test" freak out

module_dir = os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
    setup(
        name='FireWorks',
        version='1.1.5',
        description='FireWorks workflow software',
        long_description=open(os.path.join(module_dir, 'README.rst')).read(),
        url='https://github.com/materialsproject/fireworks',
        author='Anubhav Jain',
        author_email='anubhavster@gmail.com',
        license='modified BSD',
        packages=find_packages(),
        package_data={'fireworks.user_objects.queue_adapters': ['*.txt'], 'fireworks.user_objects.firetasks': ['templates/*.txt'], 'fireworks.flask_site': ['static/images/*', 'static/css/*', 'static/js/*', 'templates/*']},
        zip_safe=False,
        install_requires=['pyyaml>=3.1.0', 'pymongo>=3.0', 'Jinja2>=2.7.3',
                          'six>=1.5.2', 'monty>=0.5.6', 'python-dateutil>=2.2'],
        extras_require={'rtransfer': ['paramiko>=1.11'],
                        'newt': ['requests>=2.01'],
                        'webgui':['flask>=0.10.1', 'flask-paginate>=0.2.8'],
                        'daemon_mode':['fabric>=1.8.1'],
                        'plotting':['matplotlib>=1.1.1', 'networkx>=1.8.1']},
        classifiers=['Programming Language :: Python :: 2.7',
                     'Development Status :: 4 - Beta',
                     'Intended Audience :: Science/Research',
                     'Intended Audience :: System Administrators',
                     'Intended Audience :: Information Technology',
                     'Operating System :: OS Independent',
                     'Topic :: Other/Nonlisted Topic',
                     'Topic :: Scientific/Engineering'],
        test_suite='nose.collector',
        tests_require=['nose'],
        scripts=[os.path.join('scripts', f) for f in
                 os.listdir(os.path.join(module_dir, 'scripts'))]
    )
